import json
import logging
import time
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import call_openrouter
from app.models import Bill, BillTopic
from app.schemas import (
    ClusterOutcomes,
    RadarBill,
    RadarCluster,
    RadarResponse,
)
from app.similarity import cluster_bills
from app.services.outcome import classify_outcome
from app.services.urgency import compute_urgency

logger = logging.getLogger(__name__)

_RADAR_CACHE_TTL = 600
_RADAR_CACHE_MAX = 5
_radar_cache: dict[str, tuple[RadarResponse, float]] = {}

_VELOCITY_WINDOW_DAYS = 90
_VELOCITY_MIN_BILLS = 3


def _compute_cluster_outcomes(bills: list[Bill]) -> ClusterOutcomes:
    passed = failed = pending = 0
    resolution_days: list[float] = []
    intro_dates: list[datetime] = []

    for b in bills:
        outcome = classify_outcome(b.status, b.passed_date)
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        else:
            pending += 1

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


def _build_radar(db: Session, topic: str | None, min_cities: int) -> RadarResponse:
    query = db.query(Bill)
    if topic:
        query = query.join(BillTopic, BillTopic.bill_id == Bill.id).filter(
            BillTopic.topic_name == topic,
        )

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
                urgency=compute_urgency(b),
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

            raw = call_openrouter(
                prompt, temperature=0.2, response_format={"type": "json_object"},
            )
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
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "cluster_insight_generation_failed",
                extra={"error": str(exc)[:200]},
            )

    return RadarResponse(
        clusters=clusters,
        total_clusters=len(clusters),
        total_bills=total_bills,
    )


def build_radar(db: Session, topic: str | None, min_cities: int) -> RadarResponse:
    cache_key = topic or "__all__"
    now = time.time()

    if cache_key in _radar_cache:
        cached_response, cached_at = _radar_cache[cache_key]
        if (now - cached_at) < _RADAR_CACHE_TTL:
            return cached_response

    response = _build_radar(db, topic, min_cities)
    _radar_cache[cache_key] = (response, now)
    if len(_radar_cache) > _RADAR_CACHE_MAX:
        oldest_key = min(_radar_cache, key=lambda k: _radar_cache[k][1])
        del _radar_cache[oldest_key]
    return response
