import json
import logging
import time

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import call_openrouter
from app.models import Bill, BillTopic

logger = logging.getLogger(__name__)

VALID_TOPICS = [
    "housing",
    "policing",
    "labor",
    "environment",
    "education",
    "transit",
    "healthcare",
    "budget",
    "zoning",
    "civil_rights",
    "immigration",
    "guns",
    "elections",
    "technology",
    "public_safety",
    "social_services",
    "infrastructure",
    "taxes",
    "business_regulation",
    "other",
]

SYSTEM_PROMPT = f"""You are a legislative bill classifier. Given a list of bill titles, assign 1-3 topic tags to each bill from ONLY this list:

{json.dumps(VALID_TOPICS)}

Respond with a JSON object mapping each bill ID to a list of topics. Example:
{{"1": ["housing", "zoning"], "2": ["policing", "public_safety"]}}

Rules:
- Use ONLY topics from the provided list
- Assign 1-3 topics per bill based on the title
- If a bill doesn't clearly fit any topic, use ["other"]
- Respond with ONLY the JSON object, no other text"""


def _replace_topic_links(session: Session, bill_id: int, topics: list[str]) -> None:
    """Atomically replace BillTopic rows for a bill with the given topics."""
    session.query(BillTopic).filter(BillTopic.bill_id == bill_id).delete(
        synchronize_session=False,
    )
    for topic in topics:
        session.add(BillTopic(bill_id=bill_id, topic_name=topic))


def _classify_bills(bills: list[dict]) -> dict:
    """Send a batch of bills to OpenRouter for topic classification. Returns parsed JSON dict."""
    bill_lines = "\n".join(f"ID {b['id']}: {b['title']}" for b in bills)
    user_prompt = f"Classify these bills:\n\n{bill_lines}"

    raw = call_openrouter(
        user_prompt,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.1,
        timeout=60.0,
        response_format={"type": "json_object"},
    )
    return json.loads(raw)


def tag_untagged_bills(session: Session, batch_size: int = 20) -> int:
    """Tag a batch of untagged bills. Returns count of bills tagged."""
    untagged = (
        session.query(Bill)
        .filter(Bill.topics.is_(None))
        .limit(batch_size)
        .all()
    )

    if not untagged:
        return 0

    bills_data = [{"id": b.id, "title": b.title} for b in untagged]
    bill_map = {b.id: b for b in untagged}

    try:
        classifications = _classify_bills(bills_data)
    except httpx.HTTPError as exc:
        logger.error(
            "tagging_api_error",
            extra={
                "error": str(exc)[:200],
                "count": len(bills_data),
            },
        )
        return 0
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.error(
            "tagging_parse_error",
            extra={
                "error": str(exc)[:200],
                "count": len(bills_data),
            },
        )
        # Mark these bills with empty topics to avoid infinite retries
        for bill in untagged:
            bill.topics = "[]"
            _replace_topic_links(session, bill.id, [])
        session.commit()
        return len(untagged)

    tagged = 0
    for bill_id_str, topics in classifications.items():
        try:
            bill_id = int(bill_id_str)
        except ValueError:
            continue

        bill = bill_map.get(bill_id)
        if not bill:
            continue

        valid = [t for t in topics if t in VALID_TOPICS]
        if not valid:
            valid = ["other"]

        bill.topics = json.dumps(valid)
        _replace_topic_links(session, bill_id, valid)
        tagged += 1

    for bill in untagged:
        if bill.topics is None:
            bill.topics = "[]"
            _replace_topic_links(session, bill.id, [])

    session.commit()

    logger.info(
        "tagging_batch_completed",
        extra={
            "bills_tagged": tagged,
            "count": len(bills_data),
        },
    )

    return tagged


def tag_all_untagged_bills(session: Session) -> int:
    """Tag all untagged bills in batches. Returns total count tagged."""
    if not settings.OPENROUTER_API_KEY:
        logger.info("tagging_skipped_no_key")
        return 0

    total_tagged = 0
    while True:
        tagged = tag_untagged_bills(session, batch_size=20)
        if tagged == 0:
            break
        total_tagged += tagged
        time.sleep(0.5)

    logger.info(
        "tagging_all_completed",
        extra={"bills_tagged": total_tagged},
    )
    return total_tagged
