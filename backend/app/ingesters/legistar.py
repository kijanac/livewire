import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.ingesters.base import BaseIngester
from app.models import Bill

logger = logging.getLogger(__name__)


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-format datetime string from Legistar, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class LegistarIngester(BaseIngester):
    def __init__(self, city_key: str, city_config: dict, base_url: str) -> None:
        self.city_key = city_key
        self.city_name = city_config["name"]
        self.state = city_config["state"]
        self.base_url = base_url

    def ingest(self, session: Session) -> tuple[int, int]:
        """Fetch matters from Legistar and upsert into the database.

        Returns (added_count, updated_count).
        """
        added = 0
        updated = 0

        one_year_ago = (datetime.now(tz=timezone.utc) - timedelta(days=365)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        url = f"{self.base_url}/{self.city_key}/matters"
        params = {
            "$top": 250,
            "$orderby": "MatterLastModifiedUtc desc",
            "$filter": f"MatterLastModifiedUtc ge datetime'{one_year_ago}'",
        }

        logger.info(
            "Legistar ingestion started",
            extra={
                "event": "ingestion_started",
                "city": self.city_key,
                "city_name": self.city_name,
                "url": url,
            },
        )

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                matters = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Legistar API returned an error status",
                extra={
                    "event": "ingestion_api_error",
                    "city": self.city_key,
                    "status_code": exc.response.status_code,
                    "url": url,
                },
            )
            return added, updated
        except httpx.RequestError as exc:
            logger.error(
                "Legistar API request failed",
                extra={
                    "event": "ingestion_request_error",
                    "city": self.city_key,
                    "error": str(exc),
                    "url": url,
                },
            )
            return added, updated

        if not isinstance(matters, list):
            logger.warning(
                "Unexpected response format from Legistar API",
                extra={
                    "event": "ingestion_unexpected_response",
                    "city": self.city_key,
                    "response_type": type(matters).__name__,
                },
            )
            return added, updated

        for matter in matters:
            source_id = str(matter.get("MatterId", ""))
            if not source_id:
                continue

            title = matter.get("MatterTitle") or matter.get("MatterName") or ""
            if not title:
                continue

            bill_url = (
                f"https://{self.city_key}.legistar.com"
                f"/gateway.aspx?m=l&id={source_id}"
            )

            bill_data = {
                "source": "legistar",
                "source_id": source_id,
                "city": self.city_key,
                "city_name": self.city_name,
                "state": self.state,
                "file_number": matter.get("MatterFile"),
                "title": title,
                "type_name": matter.get("MatterTypeName"),
                "status": matter.get("MatterStatusName"),
                "body_name": matter.get("MatterBodyName"),
                "intro_date": _parse_datetime(matter.get("MatterIntroDate")),
                "agenda_date": _parse_datetime(matter.get("MatterAgendaDate")),
                "passed_date": _parse_datetime(matter.get("MatterPassedDate")),
                "enactment_number": matter.get("MatterEnactmentNumber"),
                "enactment_date": _parse_datetime(matter.get("MatterEnactmentDate")),
                "updated_at": _parse_datetime(matter.get("MatterLastModifiedUtc")),
                "url": bill_url,
            }

            existing = (
                session.query(Bill)
                .filter_by(source="legistar", source_id=source_id, city=self.city_key)
                .first()
            )

            if existing:
                for key, value in bill_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                session.add(Bill(**bill_data))
                added += 1

        session.commit()

        logger.info(
            "Legistar ingestion completed",
            extra={
                "event": "ingestion_completed",
                "city": self.city_key,
                "city_name": self.city_name,
                "bills_added": added,
                "bills_updated": updated,
                "total_matters": len(matters),
            },
        )

        return added, updated
