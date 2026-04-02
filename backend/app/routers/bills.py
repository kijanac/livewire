import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import SessionLocal, get_db
from app.ingesters.legistar import LegistarIngester
from app.models import Bill, BillAction, BillBriefing, CollectionItem, Official, VoteRecord, bill_sponsors
from app.schemas import (
    ActionResponse,
    BillBriefingResponse,
    BillListResponse,
    BillResponse,
    CityActivity,
    CityCount,
    CityResponse,
    IngestRequest,
    IngestResponse,
    NewsArticle,
    OfficialResponse,
    PowerSection,
    RadarBill,
    RadarCluster,
    RadarResponse,
    SimilarBill,
    StatsResponse,
    StatusCount,
    TopicCount,
    VoteRecordResponse,
    VoteSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def compute_urgency(agenda_date: datetime | None) -> str:
    if not agenda_date:
        return "normal"
    now = datetime.now(tz=timezone.utc)
    if agenda_date.tzinfo is None:
        agenda_date = agenda_date.replace(tzinfo=timezone.utc)
    delta = (agenda_date - now).days
    if delta < 0:
        return "normal"
    if delta <= 7:
        return "urgent"
    if delta <= 30:
        return "soon"
    return "normal"


def bill_to_response(bill: Bill, summary: str | None = None) -> BillResponse:
    response = BillResponse.model_validate(bill)
    response.urgency = compute_urgency(bill.agenda_date)
    response.summary = summary
    return response


def _attach_summaries(
    bills: list[Bill], db: Session
) -> list[BillResponse]:
    """Convert bills to responses with cached briefing summaries attached."""
    bill_ids = [b.id for b in bills]
    if not bill_ids:
        return []
    briefings = (
        db.query(BillBriefing.bill_id, BillBriefing.summary)
        .filter(BillBriefing.bill_id.in_(bill_ids))
        .all()
    )
    summary_map = {bid: s for bid, s in briefings}
    return [bill_to_response(b, summary_map.get(b.id)) for b in bills]


@router.get("/topics", response_model=list[str])
def list_topics() -> list[str]:
    from app.tagger import VALID_TOPICS

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


# Radar response cache: keyed by topic, stores (response, timestamp)
import time as _time

_radar_cache: dict[str, tuple[RadarResponse, float]] = {}
_RADAR_CACHE_TTL = 600  # 10 minutes


def _build_radar(topic: str | None, min_cities: int, db: Session) -> RadarResponse:
    """Build radar response with clustering and LLM labels."""
    import json as _json

    from app.similarity import cluster_bills

    query = db.query(Bill)
    if topic:
        query = query.filter(Bill.topics.like(f'%"{topic}"%'))

    bills = query.all()
    bill_map = {b.id: b for b in bills}
    bill_ids = [b.id for b in bills]

    if len(bill_ids) < 2:
        return RadarResponse(clusters=[], total_clusters=0, total_bills=0)

    raw_clusters = cluster_bills(bill_ids, distance_threshold=0.7)

    clusters = []
    total_bills = 0
    for rc in raw_clusters:
        cluster_bills_objs = [bill_map[bid] for bid in rc["bill_ids"] if bid in bill_map]
        unique_cities = list({b.city_name for b in cluster_bills_objs})

        if len(unique_cities) < min_cities:
            continue

        radar_bills = []
        for b in cluster_bills_objs:
            topics = []
            if b.topics:
                try:
                    topics = _json.loads(b.topics)
                except (ValueError, TypeError):
                    pass
            radar_bills.append(RadarBill(
                id=b.id,
                city=b.city,
                city_name=b.city_name,
                state=b.state,
                title=b.title,
                file_number=b.file_number,
                status=b.status,
                type_name=b.type_name,
                topics=topics,
                urgency=compute_urgency(b.agenda_date),
                intro_date=b.intro_date,
                url=b.url,
            ))

        clusters.append(RadarCluster(
            label=rc["label"],
            top_terms=rc["top_terms"],
            cities=sorted(unique_cities),
            city_count=len(unique_cities),
            bill_count=len(radar_bills),
            bills=radar_bills,
        ))
        total_bills += len(radar_bills)

    # Generate human-readable cluster labels via LLM
    if clusters and settings.OPENROUTER_API_KEY:
        try:
            import httpx

            cluster_descriptions = []
            for i, c in enumerate(clusters):
                titles = [b.title[:80] for b in c.bills[:4]]
                cluster_descriptions.append(
                    f"Cluster {i + 1} ({', '.join(c.cities)}): "
                    + " | ".join(titles)
                )

            prompt = (
                "For each cluster of related city council bills below, write a short "
                "human-readable label (3-6 words) that an organizer would use. "
                "Return a JSON array of strings, one label per cluster.\n\n"
                + "\n".join(cluster_descriptions)
            )

            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(settings.OPENROUTER_BASE_URL, json=payload, headers=headers)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = _json.loads(content)
                labels_list = parsed if isinstance(parsed, list) else parsed.get("labels", [])
                for i, label in enumerate(labels_list):
                    if i < len(clusters):
                        clusters[i].label = str(label)
        except Exception as exc:
            logger.warning(
                "Failed to generate cluster labels",
                extra={"event": "cluster_label_generation_failed", "error": str(exc)},
            )

    return RadarResponse(
        clusters=clusters,
        total_clusters=len(clusters),
        total_bills=total_bills,
    )


@router.get("/bills/radar", response_model=RadarResponse)
def get_bill_radar(
    topic: str | None = Query(None),
    min_cities: int = Query(2, ge=2),
    db: Session = Depends(get_db),
) -> RadarResponse:
    cache_key = topic or "__all__"
    now = _time.time()

    # Return cached response if fresh
    if cache_key in _radar_cache:
        cached_response, cached_at = _radar_cache[cache_key]
        if (now - cached_at) < _RADAR_CACHE_TTL:
            return cached_response

    response = _build_radar(topic, min_cities, db)
    _radar_cache[cache_key] = (response, now)
    return response


def _build_power_section(db: Session, bill: Bill, briefing: BillBriefing) -> PowerSection:
    """Build the power intelligence section for a bill."""
    city_config = settings.CITIES.get(bill.city)
    if city_config and not bill.enriched_at:
        ingester = LegistarIngester(
            city_key=bill.city,
            city_config=city_config,
            base_url=settings.LEGISTAR_BASE_URL,
        )
        ingester.enrich_bill(db, bill)

    sponsor_rows = (
        db.query(Official)
        .join(bill_sponsors, bill_sponsors.c.official_id == Official.id)
        .filter(bill_sponsors.c.bill_id == bill.id)
        .all()
    )
    sponsors = [OfficialResponse.model_validate(o) for o in sponsor_rows]

    vote_records = (
        db.query(VoteRecord)
        .options(selectinload(VoteRecord.official))
        .filter(VoteRecord.bill_id == bill.id)
        .all()
    )
    votes = None
    if vote_records:
        counts = {"yea": 0, "nay": 0, "abstain": 0, "absent": 0, "other": 0}
        records = []
        for vr in vote_records:
            counts[vr.vote_value] = counts.get(vr.vote_value, 0) + 1
            records.append(VoteRecordResponse(
                official=vr.official.name if vr.official else "Unknown",
                vote=vr.vote_value or "",
                district=vr.official.district if vr.official else None,
            ))
        votes = VoteSummary(**counts, records=records)

    action_rows = (
        db.query(BillAction)
        .options(selectinload(BillAction.mover), selectinload(BillAction.seconder))
        .filter(BillAction.bill_id == bill.id)
        .order_by(BillAction.action_date.asc())
        .all()
    )
    actions = [
        ActionResponse(
            date=a.action_date.isoformat() if a.action_date else None,
            action=a.action_text,
            body=a.body_name,
            result=a.result,
            mover=a.mover.name if a.mover else None,
            seconder=a.seconder.name if a.seconder else None,
        )
        for a in action_rows
    ]

    analysis = briefing.power_analysis
    if not analysis and (sponsors or vote_records or action_rows) and settings.OPENROUTER_API_KEY:
        analysis = _generate_power_analysis(bill, sponsors, votes, actions)
        briefing.power_analysis = analysis
        db.commit()

    return PowerSection(
        sponsors=sponsors,
        votes=votes,
        actions=actions,
        analysis=analysis,
    )


def _generate_power_analysis(
    bill: Bill,
    sponsors: list[OfficialResponse],
    votes: VoteSummary | None,
    actions: list[ActionResponse],
) -> str:
    """Generate an AI power analysis for a bill."""
    from app.briefing import call_openrouter

    sponsor_text = ", ".join(s.name for s in sponsors) if sponsors else "No sponsors listed"
    vote_text = "No votes recorded"
    if votes:
        vote_text = f"Yea: {votes.yea}, Nay: {votes.nay}, Abstain: {votes.abstain}, Absent: {votes.absent}"
        if votes.records:
            nay_names = [r.official for r in votes.records if r.vote == "nay"]
            if nay_names:
                vote_text += f". Voted no: {', '.join(nay_names)}"

    action_text = "No action history"
    if actions:
        recent = actions[-5:]
        action_text = "; ".join(
            f"{a.date or '?'}: {a.action or '?'} ({a.body or '?'})" + (f" — {a.result}" if a.result else "")
            for a in recent
        )

    prompt = (
        "You are a political intelligence analyst for community organizers. "
        "Given the following data about a legislative bill, write a 2-4 sentence power analysis. "
        "Focus on: who controls this bill's fate, any notable voting patterns, "
        "and strategic observations an organizer should know. "
        "Be direct and actionable, not speculative.\n\n"
        f"Bill: {bill.title}\n"
        f"City: {bill.city_name}, {bill.state}\n"
        f"Status: {bill.status or 'Unknown'}\n"
        f"Committee/Body: {bill.body_name or 'Unknown'}\n"
        f"Sponsors: {sponsor_text}\n"
        f"Vote tally: {vote_text}\n"
        f"Recent actions: {action_text}\n\n"
        "Write ONLY the analysis paragraph, no headers or formatting."
    )

    try:
        return call_openrouter(prompt, max_tokens=300).strip()
    except Exception as exc:
        logger.error(
            "Power analysis generation failed",
            extra={"event": "power_analysis_failed", "bill_id": bill.id, "error": str(exc)},
        )
        return ""


@router.get("/bills/{bill_id}/briefing", response_model=BillBriefingResponse)
def get_bill_briefing(
    bill_id: int,
    db: Session = Depends(get_db),
) -> BillBriefingResponse:
    import json as _json

    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    from app.briefing import get_or_create_briefing

    briefing = get_or_create_briefing(db, bill)

    # Parse cached news
    news = []
    if briefing.news_json:
        try:
            news = [NewsArticle(**a) for a in _json.loads(briefing.news_json)]
        except (ValueError, TypeError):
            pass

    # Find similar bills via TF-IDF cosine similarity
    similar_bills = []
    from app.similarity import find_similar_bills

    similar_ids_scores = find_similar_bills(bill.id, n=8)
    if similar_ids_scores:
        # Filter to different cities only, keep top 5
        similar_bill_ids = [bid for bid, _ in similar_ids_scores]
        similar_objs = (
            db.query(Bill)
            .filter(Bill.id.in_(similar_bill_ids), Bill.city != bill.city)
            .all()
        )
        # Preserve similarity score ordering
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

    # Build timeline from bill dates
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

    # Get collection notes for this bill
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

    # Build power intelligence section
    power = _build_power_section(db, bill, briefing)

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
        power=power,
    )


@router.get("/bills", response_model=BillListResponse)
def list_bills(
    city: str | None = Query(None),
    status: str | None = Query(None),
    type_name: str | None = Query(None),
    topic: str | None = Query(None),
    urgency: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> BillListResponse:
    query = db.query(Bill)

    if city:
        query = query.filter(Bill.city == city)
    if status:
        query = query.filter(Bill.status == status)
    if type_name:
        query = query.filter(Bill.type_name == type_name)
    if topic:
        query = query.filter(Bill.topics.like(f'%"{topic}"%'))
    if search:
        query = query.filter(Bill.title.ilike(f"%{search}%"))

    # Urgency filters translate to date range queries on agenda_date
    if urgency == "urgent":
        now = datetime.now(tz=timezone.utc)
        cutoff = now + timedelta(days=7)
        query = query.filter(
            Bill.agenda_date.isnot(None),
            Bill.agenda_date >= now,
            Bill.agenda_date <= cutoff,
        )
    elif urgency == "soon":
        now = datetime.now(tz=timezone.utc)
        cutoff_7 = now + timedelta(days=7)
        cutoff_30 = now + timedelta(days=30)
        query = query.filter(
            Bill.agenda_date.isnot(None),
            Bill.agenda_date > cutoff_7,
            Bill.agenda_date <= cutoff_30,
        )

    total = query.count()

    # Order by intro_date desc (nulls last), then updated_at desc
    query = query.order_by(
        case((Bill.intro_date.is_(None), 1), else_=0),
        Bill.intro_date.desc(),
        Bill.updated_at.desc(),
    )

    offset = (page - 1) * per_page
    bills = query.offset(offset).limit(per_page).all()

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
    return [
        CityResponse(id=key, name=cfg["name"], state=cfg["state"])
        for key, cfg in settings.CITIES.items()
    ]


_stats_cache: tuple[StatsResponse, float] | None = None
_STATS_CACHE_TTL = 300  # 5 minutes


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    import json as _json

    global _stats_cache
    now_ts = _time.time()
    if _stats_cache and (now_ts - _stats_cache[1]) < _STATS_CACHE_TTL:
        return _stats_cache[0]

    now = datetime.now(tz=timezone.utc)
    week_from_now = now + timedelta(days=7)
    week_ago = now - timedelta(days=7)

    # Bills moving this week: agenda date within next 7 days
    moving_this_week = (
        db.query(func.count(Bill.id))
        .filter(Bill.agenda_date.isnot(None), Bill.agenda_date >= now, Bill.agenda_date <= week_from_now)
        .scalar()
    ) or 0

    # New bills introduced in the last 7 days
    new_bills_7d = (
        db.query(func.count(Bill.id))
        .filter(Bill.intro_date.isnot(None), Bill.intro_date >= week_ago)
        .scalar()
    ) or 0

    # Hot topics: most common topics across bills with upcoming agenda dates or recent introductions
    active_bills = (
        db.query(Bill.topics)
        .filter(
            Bill.topics.isnot(None),
            Bill.topics != "[]",
        )
        .all()
    )
    topic_counts: dict[str, int] = {}
    for (topics_json,) in active_bills:
        try:
            for t in _json.loads(topics_json):
                if t != "other":
                    topic_counts[t] = topic_counts.get(t, 0) + 1
        except (ValueError, TypeError):
            continue
    hot_topics = [
        TopicCount(topic=t, count=c)
        for t, c in sorted(topic_counts.items(), key=lambda x: -x[1])[:3]
    ]

    # Most active city: city with most bills that have upcoming agenda dates
    city_upcoming_rows = (
        db.query(Bill.city, Bill.city_name, func.count(Bill.id).label("cnt"))
        .filter(Bill.agenda_date.isnot(None), Bill.agenda_date >= now)
        .group_by(Bill.city, Bill.city_name)
        .order_by(func.count(Bill.id).desc())
        .first()
    )
    most_active_city = None
    if city_upcoming_rows:
        most_active_city = CityActivity(
            city=city_upcoming_rows[0],
            city_name=city_upcoming_rows[1],
            upcoming_count=city_upcoming_rows[2],
        )

    # Bills grouped by status (top 10) — kept for filters/reference
    status_rows = (
        db.query(Bill.status, func.count(Bill.id).label("count"))
        .filter(Bill.status.isnot(None))
        .group_by(Bill.status)
        .order_by(func.count(Bill.id).desc())
        .limit(10)
        .all()
    )
    by_status = [StatusCount(status=row[0], count=row[1]) for row in status_rows]

    # Bills grouped by city
    city_rows = (
        db.query(Bill.city, Bill.city_name, func.count(Bill.id).label("count"))
        .group_by(Bill.city, Bill.city_name)
        .order_by(func.count(Bill.id).desc())
        .all()
    )
    by_city = [
        CityCount(city=row[0], city_name=row[1], count=row[2]) for row in city_rows
    ]

    result = StatsResponse(
        moving_this_week=moving_this_week,
        hot_topics=hot_topics,
        most_active_city=most_active_city,
        new_bills_7d=new_bills_7d,
        by_status=by_status,
        by_city=by_city,
    )
    _stats_cache = (result, _time.time())
    return result


@router.post("/ingest", response_model=IngestResponse)
def run_ingest(
    body: IngestRequest | None = None,
) -> IngestResponse:
    total_added = 0
    total_updated = 0

    if body and body.city:
        cities_to_ingest = {body.city: settings.CITIES.get(body.city)}
        if not cities_to_ingest[body.city]:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown city: {body.city}",
            )
    else:
        cities_to_ingest = settings.CITIES

    for city_key, city_config in cities_to_ingest.items():
        ingester = LegistarIngester(
            city_key=city_key,
            city_config=city_config,
            base_url=settings.LEGISTAR_BASE_URL,
        )
        session = SessionLocal()
        try:
            added, updated = ingester.ingest(session)
            total_added += added
            total_updated += updated
        except Exception:
            logger.exception(
                "Ingestion failed for city",
                extra={
                    "event": "ingestion_failed",
                    "city": city_key,
                },
            )
        finally:
            session.close()

    return IngestResponse(
        message="Ingestion complete",
        bills_added=total_added,
        bills_updated=total_updated,
    )


@router.post("/tag", response_model=dict)
def run_tagging() -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=400, detail="OPENROUTER_API_KEY not configured"
        )
    from app.tagger import tag_all_untagged_bills

    session = SessionLocal()
    try:
        tagged = tag_all_untagged_bills(session)
        return {"message": "Tagging complete", "bills_tagged": tagged}
    finally:
        session.close()
