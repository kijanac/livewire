import json
import logging
import time
from collections import defaultdict

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import call_openrouter
from app.models import Bill, BillBriefing, BillTopic
from app.schemas import (
    CityAlignment,
    CoalitionBrief,
    CoalitionsResponse,
    SimilarBill,
    TopicCoalition,
)
from app.services.outcome import _FAILED_STATUSES, _PASSED_STATUSES, classify_outcome

logger = logging.getLogger(__name__)

_coalitions_cache: dict[str, tuple[CoalitionsResponse, float]] = {}
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
    rows = (
        db.query(
            BillTopic.topic_name,
            Bill.city,
            Bill.city_name,
            Bill.status,
            Bill.passed_date,
        )
        .join(Bill, Bill.id == BillTopic.bill_id)
        .all()
    )

    topic_city: dict[str, dict[str, dict]] = defaultdict(
        lambda: defaultdict(lambda: {"city": "", "city_name": "", "p": 0, "f": 0, "pe": 0})
    )

    for topic, city, city_name, status, passed_date in rows:
        outcome = classify_outcome(status, passed_date)
        entry = topic_city[topic][city]
        entry["city"] = city
        entry["city_name"] = city_name
        if outcome == "passed":
            entry["p"] += 1
        elif outcome == "failed":
            entry["f"] += 1
        else:
            entry["pe"] += 1

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
            raw = call_openrouter(
                prompt, temperature=0.2, response_format={"type": "json_object"},
            )
            parsed = json.loads(raw)
            insights = parsed.get("insights", [])
            for i, insight in enumerate(insights):
                if i < len(top_topics):
                    top_topics[i].insight = str(insight)
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "coalition_insight_failed",
                extra={"error": str(exc)[:200]},
            )

    return CoalitionsResponse(
        topics=topic_coalitions,
        total_topics=len(topic_coalitions),
    )


def build_coalitions(db: Session) -> CoalitionsResponse:
    now = time.time()
    if "__all__" in _coalitions_cache:
        cached_response, cached_at = _coalitions_cache["__all__"]
        if (now - cached_at) < _COALITIONS_CACHE_TTL:
            return cached_response

    response = _build_coalitions(db)
    _coalitions_cache["__all__"] = (response, now)
    return response


def build_coalition_brief(
    db: Session, bill: Bill, briefing: BillBriefing, similar_bills: list[SimilarBill],
) -> CoalitionBrief | None:
    if not similar_bills:
        return None

    if briefing.coalition_json:
        try:
            return CoalitionBrief(**json.loads(briefing.coalition_json))
        except (ValueError, TypeError):
            pass

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
            insight = call_openrouter(prompt, temperature=0.3, max_tokens=200).strip()
        except httpx.HTTPError as exc:
            logger.warning(
                "coalition_brief_failed",
                extra={"bill_id": bill.id, "error": str(exc)[:200]},
            )

    if not ally_cities and not contested_cities and not insight:
        return None

    result = CoalitionBrief(
        ally_cities=ally_cities,
        contested_cities=contested_cities,
        insight=insight,
    )

    briefing.coalition_json = json.dumps(result.model_dump())
    db.commit()

    return result
