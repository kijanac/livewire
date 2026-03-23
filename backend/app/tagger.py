import json
import logging
import time

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Bill

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


def _call_openrouter(bills: list[dict]) -> dict:
    """Send a batch of bills to OpenRouter for topic classification."""
    bill_lines = "\n".join(f"ID {b['id']}: {b['title']}" for b in bills)
    user_prompt = f"Classify these bills:\n\n{bill_lines}"

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            settings.OPENROUTER_BASE_URL,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


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
        result = _call_openrouter(bills_data)
        content = result["choices"][0]["message"]["content"]
        classifications = json.loads(content)
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        logger.error(
            "OpenRouter API call failed",
            extra={
                "event": "tagging_api_error",
                "error": str(exc),
                "batch_size": len(bills_data),
            },
        )
        return 0
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.error(
            "Failed to parse tagging response",
            extra={
                "event": "tagging_parse_error",
                "error": str(exc),
                "batch_size": len(bills_data),
            },
        )
        # Mark these bills with empty topics to avoid infinite retries
        for bill in untagged:
            bill.topics = "[]"
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

        # Validate topics against allowed list
        valid = [t for t in topics if t in VALID_TOPICS]
        if not valid:
            valid = ["other"]

        bill.topics = json.dumps(valid)
        tagged += 1

    # Mark any bills that weren't in the response
    for bill in untagged:
        if bill.topics is None:
            bill.topics = "[]"

    session.commit()

    logger.info(
        "Topic tagging batch completed",
        extra={
            "event": "tagging_batch_completed",
            "bills_tagged": tagged,
            "batch_size": len(bills_data),
        },
    )

    return tagged


def tag_all_untagged_bills(session: Session) -> int:
    """Tag all untagged bills in batches. Returns total count tagged."""
    if not settings.OPENROUTER_API_KEY:
        logger.info(
            "Skipping tagging, no API key configured",
            extra={"event": "tagging_skipped_no_key"},
        )
        return 0

    total_tagged = 0
    while True:
        tagged = tag_untagged_bills(session, batch_size=20)
        if tagged == 0:
            break
        total_tagged += tagged
        time.sleep(0.5)

    logger.info(
        "Topic tagging completed",
        extra={
            "event": "tagging_all_completed",
            "total_bills_tagged": total_tagged,
        },
    )
    return total_tagged
