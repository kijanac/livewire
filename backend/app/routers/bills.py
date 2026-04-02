import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session, selectinload

from app.briefing import call_openrouter, get_or_create_briefing
from app.config import settings
from app.similarity import cluster_bills, find_similar_bills
from app.database import SessionLocal, get_db
from app.ingesters.legistar import LegistarIngester
from app.models import Bill, BillAction, BillBriefing, CollectionItem, Official, VoteRecord, bill_sponsors
from app.schemas import (
    ActionResponse,
    BillBriefingResponse,
    BillListResponse,
    BillResponse,
    CityActivity,
    CityAlignment,
    CityCount,
    CityResponse,
    ClusterOutcomes,
    CoalitionBrief,
    CoalitionsResponse,
    IngestRequest,
    IngestResponse,
    NarrativeSection,
    NewsArticle,
    NewsFrame,
    OfficialResponse,
    PowerSection,
    RadarBill,
    RadarCluster,
    RadarResponse,
    SimilarBill,
    StatsResponse,
    StatusCount,
    TopicCoalition,
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

# --- Outcome classification for Pattern Intelligence ---
_PASSED_STATUSES = frozenset({
    "passed", "adopted", "approved", "enacted", "confirmed", "granted",
    "passed finally", "passed unsigned by mayor", "passed at full council",
    "adopted as amended", "granted (with modifications)",
})
_FAILED_STATUSES = frozenset({
    "failed", "denied", "dead", "disallowed", "withdrawn", "vetoed",
    "failed - end of term", "failed to pass",
    "died due to expiration of legislative council session",
})

_VELOCITY_WINDOW_DAYS = 90
_VELOCITY_MIN_BILLS = 3


def _classify_outcome(bill: "Bill") -> str:
    """Classify a bill as passed/failed/pending from its status."""
    if bill.passed_date:
        return "passed"
    s = (bill.status or "").strip().lower()
    if s in _PASSED_STATUSES:
        return "passed"
    if s in _FAILED_STATUSES:
        return "failed"
    return "pending"


def _compute_cluster_outcomes(bills: list["Bill"]) -> ClusterOutcomes:
    """Compute outcome stats for a cluster of bills."""
    passed = failed = pending = 0
    resolution_days: list[float] = []
    intro_dates: list[datetime] = []

    for b in bills:
        outcome = _classify_outcome(b)
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        else:
            pending += 1

        # Resolution time: intro_date → passed_date (or use a proxy end date)
        end = b.passed_date or b.enactment_date
        if b.intro_date and end:
            delta = (end - b.intro_date).days
            if delta >= 0:
                resolution_days.append(delta)

        if b.intro_date:
            intro_dates.append(b.intro_date)

    avg_days = round(sum(resolution_days) / len(resolution_days), 1) if resolution_days else None

    intro_dates.sort()
    earliest = intro_dates[0].isoformat() if intro_dates else None
    latest = intro_dates[-1].isoformat() if intro_dates else None
    span_days = (intro_dates[-1] - intro_dates[0]).days if len(intro_dates) >= 2 else None

    velocity_flag = (
        span_days is not None
        and span_days <= _VELOCITY_WINDOW_DAYS
        and len(intro_dates) >= _VELOCITY_MIN_BILLS
    )

    return ClusterOutcomes(
        passed=passed,
        failed=failed,
        pending=pending,
        avg_days_to_resolution=avg_days,
        earliest_intro=earliest,
        latest_intro=latest,
        intro_span_days=span_days,
        velocity_flag=velocity_flag,
    )


def _build_radar(topic: str | None, min_cities: int, db: Session) -> RadarResponse:
    """Build radar response with clustering and LLM labels."""

    query = db.query(Bill)
    if topic:
        query = query.filter(Bill.topics.like(f'%"{topic}"%'))

    bills = query.all()
    bill_map = {b.id: b for b in bills}
    bill_ids = [b.id for b in bills]

    if len(bill_ids) < 2:
        return RadarResponse(clusters=[], total_clusters=0, total_bills=0)

    raw_clusters = cluster_bills(bill_ids, distance_threshold=0.35)

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
                    topics = json.loads(b.topics)
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

        outcomes = _compute_cluster_outcomes(cluster_bills_objs)

        clusters.append(RadarCluster(
            label=rc["label"],
            top_terms=rc["top_terms"],
            cities=sorted(unique_cities),
            city_count=len(unique_cities),
            bill_count=len(radar_bills),
            bills=radar_bills,
            outcomes=outcomes,
        ))
        total_bills += len(radar_bills)

    # Generate labels + outcome insights via LLM (single call)
    if clusters and settings.OPENROUTER_API_KEY:
        try:

            cluster_descriptions = []
            for i, c in enumerate(clusters):
                titles = [b.title[:80] for b in c.bills[:4]]
                o = c.outcomes
                outcome_line = ""
                if o:
                    outcome_line = (
                        f"  Outcomes: {o.passed} passed, {o.failed} failed, {o.pending} pending."
                    )
                    if o.avg_days_to_resolution is not None:
                        outcome_line += f" Avg {o.avg_days_to_resolution} days to resolution."
                    if o.velocity_flag:
                        outcome_line += (
                            f" VELOCITY ALERT: {c.bill_count} bills introduced"
                            f" across {c.city_count} cities in {o.intro_span_days} days."
                        )
                cluster_descriptions.append(
                    f"Cluster {i + 1} ({', '.join(c.cities)}):\n"
                    f"  Bills: {' | '.join(titles)}\n"
                    f"{outcome_line}"
                )

            prompt = (
                "You are an intelligence analyst for community organizers tracking "
                "city council legislation across multiple cities.\n\n"
                "For each cluster of related bills below:\n"
                "1. Write a short label (3-6 words) an organizer would use.\n"
                "2. Write a 1-2 sentence insight about what the outcome pattern means "
                "for organizers — what happened in other cities, whether this looks "
                "coordinated, and what to watch for. Be direct and actionable.\n\n"
                "Return JSON: {\"clusters\": [{\"label\": \"...\", \"insight\": \"...\"}]}\n\n"
                + "\n\n".join(cluster_descriptions)
            )

            raw = call_openrouter(prompt, temperature=0.2, json_mode=True)
            parsed = json.loads(raw)
            items = parsed.get("clusters", parsed if isinstance(parsed, list) else [])
            for i, item in enumerate(items):
                if i < len(clusters):
                    if isinstance(item, dict):
                        clusters[i].label = str(item.get("label", clusters[i].label))
                        if item.get("insight"):
                            clusters[i].outcomes.insight = str(item["insight"])
                    elif isinstance(item, str):
                        clusters[i].label = item
        except Exception as exc:
            logger.warning(
                "Failed to generate cluster labels/insights",
                extra={"event": "cluster_insight_generation_failed", "error": str(exc)},
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


# --- Coalition Intelligence ---

_coalitions_cache: tuple[CoalitionsResponse, float] | None = None
_COALITIONS_CACHE_TTL = 600


def _compute_city_momentum(passed: int, failed: int, pending: int) -> str:
    total = passed + failed + pending
    if total == 0:
        return "stable"
    pass_rate = passed / total
    if pass_rate >= 0.5:
        return "advancing"
    if failed > passed and pending < total * 0.3:
        return "stalled"
    return "stable"


def _build_coalitions(db: Session) -> CoalitionsResponse:
    """Build cross-city coalition data grouped by topic."""
    bills = db.query(
        Bill.city, Bill.city_name, Bill.topics, Bill.status, Bill.passed_date,
    ).filter(Bill.topics.isnot(None)).all()

    # Aggregate: topic → city → outcome counts
    from collections import defaultdict
    topic_city: dict[str, dict[str, dict]] = defaultdict(
        lambda: defaultdict(lambda: {"city": "", "city_name": "", "p": 0, "f": 0, "pe": 0})
    )

    for city, city_name, topics_json, status, passed_date in bills:
        try:
            topics_list = json.loads(topics_json)
        except (ValueError, TypeError):
            continue
        outcome = _classify_outcome_from_fields(status, passed_date)
        for t in topics_list:
            entry = topic_city[t][city]
            entry["city"] = city
            entry["city_name"] = city_name
            if outcome == "passed":
                entry["p"] += 1
            elif outcome == "failed":
                entry["f"] += 1
            else:
                entry["pe"] += 1

    # Build response
    topic_coalitions = []
    for topic, cities_data in topic_city.items():
        city_alignments = []
        total_p = total_f = total_pe = 0
        for entry in cities_data.values():
            p, f, pe = entry["p"], entry["f"], entry["pe"]
            total_p += p
            total_f += f
            total_pe += pe
            city_alignments.append(CityAlignment(
                city=entry["city"],
                city_name=entry["city_name"],
                passed=p,
                failed=f,
                pending=pe,
                momentum=_compute_city_momentum(p, f, pe),
            ))
        city_alignments.sort(key=lambda c: c.passed, reverse=True)

        total_bills = total_p + total_f + total_pe
        topic_momentum = _compute_city_momentum(total_p, total_f, total_pe)

        topic_coalitions.append(TopicCoalition(
            topic=topic,
            topic_label=topic.replace("_", " ").title(),
            city_count=len(city_alignments),
            bill_count=total_bills,
            total_passed=total_p,
            total_failed=total_f,
            total_pending=total_pe,
            momentum=topic_momentum,
            cities=city_alignments,
        ))

    topic_coalitions.sort(key=lambda t: t.city_count, reverse=True)

    # Generate AI insights for top topics
    if topic_coalitions and settings.OPENROUTER_API_KEY:
        try:
            top_topics = topic_coalitions[:10]
            descriptions = []
            for tc in top_topics:
                advancing = [c.city_name for c in tc.cities if c.momentum == "advancing"][:5]
                stalled = [c.city_name for c in tc.cities if c.momentum == "stalled"][:5]
                descriptions.append(
                    f"{tc.topic_label}: {tc.bill_count} bills across {tc.city_count} cities. "
                    f"{tc.total_passed} passed, {tc.total_failed} failed, {tc.total_pending} pending. "
                    f"Advancing in: {', '.join(advancing) or 'none'}. "
                    f"Stalled in: {', '.join(stalled) or 'none'}."
                )

            prompt = (
                "You are a coalition intelligence analyst for community organizers. "
                "For each policy topic below, write a 1-2 sentence insight about the "
                "cross-city landscape — who are natural allies, where is momentum, "
                "and what should organizers know. Be direct and actionable.\n\n"
                "Return JSON: {\"insights\": [\"insight for topic 1\", ...]}\n\n"
                + "\n\n".join(descriptions)
            )
            raw = call_openrouter(prompt, temperature=0.2, json_mode=True)
            parsed = json.loads(raw)
            insights = parsed.get("insights", [])
            for i, insight in enumerate(insights):
                if i < len(top_topics):
                    top_topics[i].insight = str(insight)
        except Exception as exc:
            logger.warning(
                "Coalition insight generation failed",
                extra={"event": "coalition_insight_failed", "error": str(exc)},
            )

    return CoalitionsResponse(
        topics=topic_coalitions,
        total_topics=len(topic_coalitions),
    )


def _classify_outcome_from_fields(status: str | None, passed_date: object) -> str:
    """Classify outcome from raw status + passed_date fields (no Bill object needed)."""
    if passed_date:
        return "passed"
    s = (status or "").strip().lower()
    if s in _PASSED_STATUSES:
        return "passed"
    if s in _FAILED_STATUSES:
        return "failed"
    return "pending"


@router.get("/coalitions", response_model=CoalitionsResponse)
def get_coalitions(db: Session = Depends(get_db)) -> CoalitionsResponse:
    global _coalitions_cache
    now = _time.time()
    if _coalitions_cache:
        cached_response, cached_at = _coalitions_cache
        if (now - cached_at) < _COALITIONS_CACHE_TTL:
            return cached_response

    response = _build_coalitions(db)
    _coalitions_cache = (response, now)
    return response


def _build_coalition_brief(
    bill: Bill, similar_bills: list[SimilarBill],
) -> CoalitionBrief | None:
    """Build coalition context for a bill based on similar bills in other cities."""
    if not similar_bills:
        return None

    ally_cities = [sb.city_name for sb in similar_bills if sb.status and sb.status.strip().lower() in _PASSED_STATUSES]
    contested_cities = [sb.city_name for sb in similar_bills if sb.status and sb.status.strip().lower() not in _PASSED_STATUSES and sb.status.strip().lower() not in _FAILED_STATUSES]

    insight = None
    if settings.OPENROUTER_API_KEY and similar_bills:
        try:
            sim_text = "\n".join(
                f"- {sb.city_name}, {sb.state}: \"{sb.title}\" — Status: {sb.status or 'unknown'}"
                for sb in similar_bills
            )
            prompt = (
                "You are a coalition analyst for community organizers. "
                "A city council bill has similar legislation in other cities.\n\n"
                f"Bill: {bill.title}\n"
                f"City: {bill.city_name}, {bill.state}\n\n"
                f"Similar bills in other cities:\n{sim_text}\n\n"
                "Write 1-2 sentences of actionable coalition advice: "
                "who should they connect with, what can they learn from cities that "
                "passed or failed similar bills. Be specific and direct."
            )
            insight = call_openrouter(prompt, max_tokens=200).strip()
        except Exception as exc:
            logger.warning(
                "Coalition brief generation failed",
                extra={"event": "coalition_brief_failed", "bill_id": bill.id, "error": str(exc)},
            )

    if not ally_cities and not contested_cities and not insight:
        return None

    return CoalitionBrief(
        ally_cities=ally_cities,
        contested_cities=contested_cities,
        insight=insight,
    )


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


def _build_narrative_section(
    db: Session, bill: Bill, briefing: BillBriefing, news: list[NewsArticle], actions: list[ActionResponse],
) -> NarrativeSection | None:
    """Build narrative intelligence from news headlines + bill actions."""
    if not news and not actions:
        return None

    # Return cached analysis if available
    if briefing.narrative_json:
        try:
            cached = json.loads(briefing.narrative_json)
            return NarrativeSection(**cached)
        except (ValueError, TypeError):
            pass

    if not settings.OPENROUTER_API_KEY:
        return None

    analysis = _generate_narrative_analysis(bill, news, actions)
    if not analysis:
        return None

    # Cache the result
    briefing.narrative_json = json.dumps(analysis.model_dump())
    db.commit()

    return analysis


def _generate_narrative_analysis(
    bill: Bill, news: list[NewsArticle], actions: list[ActionResponse],
) -> NarrativeSection | None:
    """Generate AI narrative frame analysis from news + actions."""
    headlines = "\n".join(
        f"- \"{a.title}\" ({a.source}, {a.date or 'undated'})"
        for a in news
    ) if news else "No news coverage found."

    action_text = "\n".join(
        f"- {a.date or '?'}: {a.action or '?'} ({a.body or '?'})"
        + (f" — Result: {a.result}" if a.result else "")
        for a in actions[-10:]
    ) if actions else "No action history."

    prompt = (
        "You are a narrative intelligence analyst for community organizers. "
        "Analyze how this bill is being framed in news coverage and official proceedings.\n\n"
        f"Bill: {bill.title}\n"
        f"City: {bill.city_name}, {bill.state}\n"
        f"Status: {bill.status or 'Unknown'}\n"
        f"Topics: {bill.topics or '[]'}\n\n"
        f"News Headlines:\n{headlines}\n\n"
        f"Recent Legislative Actions:\n{action_text}\n\n"
        "Return JSON with this structure:\n"
        "{\n"
        '  "frames": [{"source": "outlet name", "headline": "headline text", '
        '"frame": "2-4 word frame label", "stance": "support|opposition|neutral"}],\n'
        '  "support_narrative": "1-2 sentences: how supporters frame this",\n'
        '  "opposition_narrative": "1-2 sentences: how opponents frame this (or null if no opposition visible)",\n'
        '  "narrative_trajectory": "1 sentence: is the discourse shifting? In what direction?",\n'
        '  "talking_points": ["point 1", "point 2", "point 3"]\n'
        "}\n\n"
        "For frames, classify EACH news headline. For talking_points, suggest 2-3 concise "
        "points an organizer could use at a council meeting or in a flyer. Be direct."
    )

    try:
        raw = call_openrouter(prompt, json_mode=True)
        parsed = json.loads(raw)

        frames = [
            NewsFrame(
                source=f.get("source", ""),
                headline=f.get("headline", ""),
                frame=f.get("frame", ""),
                stance=f.get("stance", "neutral"),
            )
            for f in parsed.get("frames", [])
            if isinstance(f, dict)
        ]

        return NarrativeSection(
            frames=frames,
            support_narrative=parsed.get("support_narrative"),
            opposition_narrative=parsed.get("opposition_narrative"),
            narrative_trajectory=parsed.get("narrative_trajectory"),
            talking_points=parsed.get("talking_points", []),
        )
    except Exception as exc:
        logger.error(
            "Narrative analysis generation failed",
            extra={"event": "narrative_analysis_failed", "bill_id": bill.id, "error": str(exc)},
        )
        return None


@router.get("/bills/{bill_id}/briefing", response_model=BillBriefingResponse)
def get_bill_briefing(
    bill_id: int,
    db: Session = Depends(get_db),
) -> BillBriefingResponse:
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    briefing = get_or_create_briefing(db, bill)

    # Parse cached news
    news = []
    if briefing.news_json:
        try:
            news = [NewsArticle(**a) for a in json.loads(briefing.news_json)]
        except (ValueError, TypeError):
            pass

    # Find similar bills via TF-IDF cosine similarity
    similar_bills = []

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

    # Build narrative intelligence section
    narrative = _build_narrative_section(db, bill, briefing, news, power.actions if power else [])

    # Build coalition intelligence brief
    coalition = _build_coalition_brief(bill, similar_bills)

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
            for t in json.loads(topics_json):
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
