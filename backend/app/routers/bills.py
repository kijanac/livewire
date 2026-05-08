import json
import logging
import threading
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.briefing import get_or_create_briefing
from app.config import settings
from app.database import SessionLocal, get_db
from app.ingesters.legistar import LegistarIngester
from app.ingesters.legistar_html import HTMLLegistarIngester
from app.ingesters.openstates import OpenStatesIngester
from app.models import Bill, BillBriefing, BillDocument, CollectionItem
from app.schemas import (
    BillBriefingResponse,
    BillListResponse,
    BillResponse,
    CityResponse,
    CoalitionsResponse,
    DocumentResponse,
    IngestRequest,
    IngestResponse,
    NewsArticle,
    RadarResponse,
    SimilarBill,
    StatsResponse,
)
from app.services.bill_query import BillFilters, query_bills
from app.services.briefing_service import (
    _PATTERN_MAX_SIMILAR,
    build_narrative_section,
    build_power_section,
)
from app.services.coalition_service import build_coalition_brief, build_coalitions
from app.services.radar_service import build_radar
from app.services.stats_service import build_stats
from app.services.urgency import compute_urgency
from app.similarity import find_similar_bills
from app.tagger import VALID_TOPICS, tag_all_untagged_bills

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def bill_to_response(bill: Bill, summary: str | None = None) -> BillResponse:
    response = BillResponse.model_validate(bill)
    response.urgency = compute_urgency(bill)
    response.summary = summary
    return response


def _attach_summaries(bills: list[Bill], db: Session) -> list[BillResponse]:
    ids = [b.id for b in bills]
    if not ids:
        return []
    rows = db.execute(
        select(BillBriefing.bill_id, BillBriefing.summary).where(
            BillBriefing.bill_id.in_(ids)
        )
    ).all()
    summary_map = {bid: s for bid, s in rows}
    return [bill_to_response(b, summary_map.get(b.id)) for b in bills]


@router.get("/topics", response_model=list[str])
def list_topics() -> list[str]:
    return VALID_TOPICS


@router.get("/bills/upcoming", response_model=list[BillResponse])
def get_upcoming_bills(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BillResponse]:
    now = datetime.now(tz=timezone.utc)
    bills = (
        db.query(Bill)
        .filter(Bill.agenda_date.isnot(None), Bill.agenda_date >= now)
        .order_by(Bill.agenda_date.asc())
        .limit(limit)
        .all()
    )
    return [bill_to_response(b) for b in bills]


@router.get("/bills/radar", response_model=RadarResponse)
def get_bill_radar(
    topic: str | None = Query(None),
    min_cities: int = Query(2, ge=2),
    db: Session = Depends(get_db),
) -> RadarResponse:
    return build_radar(db, topic, min_cities)


@router.get("/coalitions", response_model=CoalitionsResponse)
def get_coalitions(db: Session = Depends(get_db)) -> CoalitionsResponse:
    return build_coalitions(db)


@router.get("/bills/{bill_id}/briefing", response_model=BillBriefingResponse)
def get_bill_briefing(
    bill_id: int,
    db: Session = Depends(get_db),
) -> BillBriefingResponse:
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    briefing = get_or_create_briefing(db, bill)

    news = []
    if briefing.news_json:
        try:
            news = [NewsArticle(**a) for a in json.loads(briefing.news_json)]
        except (ValueError, TypeError):
            pass

    similar_bills = []
    similar_ids_scores = find_similar_bills(bill.id, n=_PATTERN_MAX_SIMILAR)
    if similar_ids_scores:
        similar_bill_ids = [bid for bid, _ in similar_ids_scores]
        similar_objs = (
            db.query(Bill)
            .filter(Bill.id.in_(similar_bill_ids), Bill.city != bill.city)
            .all()
        )
        bill_map = {b.id: b for b in similar_objs}
        for bid, score in similar_ids_scores:
            b = bill_map.get(bid)
            if b:
                similar_bills.append(
                    SimilarBill(
                        id=b.id,
                        city_name=b.city_name,
                        state=b.state,
                        title=b.title,
                        status=b.status,
                        file_number=b.file_number,
                    )
                )
                if len(similar_bills) >= 5:
                    break

    timeline = []
    if bill.intro_date:
        timeline.append({"event": "Introduced", "date": bill.intro_date.isoformat()})
    if bill.agenda_date:
        timeline.append({"event": "Agenda", "date": bill.agenda_date.isoformat()})
    if bill.passed_date:
        timeline.append({"event": "Passed", "date": bill.passed_date.isoformat()})
    if bill.enactment_date:
        timeline.append({"event": "Enacted", "date": bill.enactment_date.isoformat()})
    timeline.sort(key=lambda x: x["date"])

    collection_notes = []
    items = (
        db.query(CollectionItem)
        .filter(CollectionItem.bill_id == bill.id, CollectionItem.note.isnot(None), CollectionItem.note != "")
        .all()
    )
    for item in items:
        if item.collection:
            collection_notes.append({
                "collection_name": item.collection.name,
                "note": item.note,
            })

    doc_rows = db.query(BillDocument).filter(BillDocument.bill_id == bill.id).all()
    documents = [DocumentResponse.model_validate(d) for d in doc_rows]

    power = build_power_section(db, bill, briefing, similar_ids_scores or [])
    narrative = build_narrative_section(db, bill, briefing, news, power.actions if power else [])
    coalition = build_coalition_brief(db, bill, briefing, similar_bills)

    return BillBriefingResponse(
        bill=bill_to_response(bill),
        summary=briefing.summary,
        impact=briefing.impact,
        organizing=briefing.organizing,
        reception=briefing.reception,
        news=news,
        similar_bills=similar_bills,
        timeline=timeline,
        collection_notes=collection_notes,
        documents=documents,
        power=power,
        narrative=narrative,
        coalition=coalition,
    )


@router.get("/bills", response_model=BillListResponse)
def list_bills(
    city: str | None = Query(None),
    status: str | None = Query(None),
    type_name: str | None = Query(None),
    topic: str | None = Query(None),
    urgency: str | None = Query(None),
    search: str | None = Query(None),
    jurisdiction_level: str | None = Query(None),
    page: int = Query(1, ge=1, le=10_000),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BillListResponse:
    filters = BillFilters(
        city=city,
        status=status,
        type_name=type_name,
        topic=topic,
        urgency=urgency,
        search=search,
        jurisdiction_level=jurisdiction_level,
        page=page,
        per_page=per_page,
    )
    bills, total = query_bills(db, filters)
    return BillListResponse(
        bills=_attach_summaries(bills, db),
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/bills/{bill_id}", response_model=BillResponse)
def get_bill(bill_id: int, db: Session = Depends(get_db)) -> BillResponse:
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill_to_response(bill)


@router.get("/cities", response_model=list[CityResponse])
def list_cities() -> list[CityResponse]:
    results: list[CityResponse] = [
        CityResponse(id=key, name=cfg["name"], state=cfg["state"], level="city")
        for key, cfg in settings.CITIES.items()
    ]
    if settings.OPENSTATES_API_KEY:
        for state_code, state_config in settings.STATES.items():
            results.append(
                CityResponse(
                    id=f"{state_code.lower()}-state",
                    name=f"{state_config['name']} State Legislature",
                    state=state_code,
                    level="state",
                )
            )
    return results


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    try:
        return build_stats(db)
    except Exception:
        logger.exception("stats_endpoint_failed")
        return StatsResponse(
            moving_this_week=0,
            hot_topics=[],
            most_active_city=None,
            new_bills_7d=0,
            by_status=[],
            by_city=[],
        )


@router.post("/ingest", response_model=None)
def run_ingest(
    background_tasks: BackgroundTasks,
    body: IngestRequest | None = None,
):
    """Queue ingestion of city and state bills. Runs in background to avoid Render timeout."""
    background_tasks.add_task(_run_ingest_background, body)
    city_count = 1 if (body and body.city) else len(settings.CITIES)
    state_count = 0 if (body and body.city) else (
        len(settings.STATES) if settings.OPENSTATES_API_KEY else 0
    )
    return {
        "message": f"Ingestion queued for {city_count} cities + {state_count} states",
        "bills_added": 0,
        "bills_updated": 0,
    }


def _run_ingest_background(body: IngestRequest | None = None) -> None:
    """Run the full ingest pipeline synchronously (called from background task)."""
    total_added = 0
    total_updated = 0

    if body and body.city:
        cities_to_ingest = {body.city: settings.CITIES.get(body.city)}
        if not cities_to_ingest[body.city]:
            logger.error("ingest_unknown_city", extra={"city": body.city})
            return
    else:
        cities_to_ingest = settings.CITIES

    for city_key, city_config in cities_to_ingest.items():
        session = SessionLocal()
        try:
            added, updated = _try_ingest_city(city_key, city_config, session)
            total_added += added
            total_updated += updated
        except Exception:
            logger.exception("ingestion_failed", extra={"city": city_key})
        finally:
            session.close()

    if not body or not body.city:
        if settings.OPENSTATES_API_KEY:
            for state_code, state_config in settings.STATES.items():
                ingester = OpenStatesIngester(
                    state_code=state_code,
                    state_name=state_config["name"],
                    base_url=settings.OPENSTATES_BASE_URL,
                    api_key=settings.OPENSTATES_API_KEY,
                )
                session = SessionLocal()
                try:
                    added, updated = ingester.ingest(session)
                    total_added += added
                    total_updated += updated
                except Exception:
                    logger.exception("openstates_ingestion_failed", extra={"state": state_code})
                finally:
                    session.close()

    logger.info(
        "ingestion_complete",
        extra={"bills_added": total_added, "bills_updated": total_updated},
    )


def _try_ingest_city(city_key: str, city_config: dict, session) -> tuple[int, int]:
    """Try API ingester first, fall back to HTML scraping."""
    api_ingester = LegistarIngester(
        city_key=city_key,
        city_config=city_config,
        base_url=settings.LEGISTAR_BASE_URL,
    )
    try:
        added, updated = api_ingester.ingest(session)
        return added, updated
    except Exception as exc:
        logger.warning(
            "api_ingest_failed_falling_back_to_html",
            extra={"city": city_key, "error": str(exc)[:200]},
        )
        session.rollback()

    html_ingester = HTMLLegistarIngester(
        city_key=city_key, city_config=city_config
    )
    return html_ingester.ingest(session)


@router.post("/tag", response_model=dict)
def run_tagging() -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=400, detail="OPENROUTER_API_KEY not configured"
        )
    session = SessionLocal()
    try:
        tagged = tag_all_untagged_bills(session)
        return {"message": "Tagging complete", "bills_tagged": tagged}
    finally:
        session.close()
