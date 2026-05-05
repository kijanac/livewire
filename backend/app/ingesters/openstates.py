import logging
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx
from sqlalchemy.orm import Session

from app.ingesters.base import BaseIngester
from app.models import Bill

logger = logging.getLogger(__name__)

_PER_PAGE = 20
_LOOKBACK_DAYS = 2
_MAX_RETRIES_ON_429 = 4
_DEFAULT_RETRY_AFTER_SECONDS = 60.0


def _parse_retry_after(value: str | None) -> float:
    """Parse the Retry-After header (seconds or HTTP-date), falling back to a default."""
    if not value:
        return _DEFAULT_RETRY_AFTER_SECONDS
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(value)
        delta = (retry_at - datetime.now(tz=timezone.utc)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError):
        return _DEFAULT_RETRY_AFTER_SECONDS


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-format datetime/date string, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _parse_date(value: str | None) -> datetime | None:
    """Parse a YYYY-MM-DD date string into a UTC datetime, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


class OpenStatesIngester(BaseIngester):
    """Fetch state-legislature bills from the OpenStates v3 API."""

    def __init__(
        self,
        state_code: str,
        state_name: str,
        base_url: str,
        api_key: str,
    ) -> None:
        self.state_code = state_code.upper()
        self.state_name = state_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.city_key = f"{state_code.lower()}-state"
        self.city_name = f"{state_name} State Legislature"

    def ingest(self, session: Session) -> tuple[int, int]:
        """Fetch recently-updated bills and upsert. Returns (added, updated)."""
        added = 0
        updated = 0

        if not self.api_key:
            logger.warning(
                "OpenStates ingestion skipped: no API key configured",
                extra={"event": "openstates_no_api_key", "state": self.state_code},
            )
            return added, updated

        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=_LOOKBACK_DAYS)).strftime(
            "%Y-%m-%d"
        )
        url = f"{self.base_url}/bills"

        logger.info(
            "OpenStates ingestion started",
            extra={
                "event": "openstates_ingestion_started",
                "state": self.state_code,
                "state_name": self.state_name,
                "updated_since": cutoff,
            },
        )

        page = 1
        total_seen = 0
        with httpx.Client(timeout=30.0) as client:
            while True:
                params = {
                    "jurisdiction": self.state_name,
                    "updated_since": cutoff,
                    "sort": "updated_desc",
                    "page": page,
                    "per_page": _PER_PAGE,
                }
                payload = self._fetch_page(client, url, params)
                if payload is None:
                    break

                results = payload.get("results", [])
                if not results:
                    break

                for bill in results:
                    if self._upsert_bill(session, bill):
                        added += 1
                    else:
                        updated += 1
                    total_seen += 1

                session.commit()

                pagination = payload.get("pagination", {})
                max_page = pagination.get("max_page", page)
                if page >= max_page:
                    break
                page += 1

        logger.info(
            "OpenStates ingestion completed",
            extra={
                "event": "openstates_ingestion_completed",
                "state": self.state_code,
                "state_name": self.state_name,
                "bills_added": added,
                "bills_updated": updated,
                "total_seen": total_seen,
            },
        )

        return added, updated

    def _fetch_page(
        self, client: httpx.Client, url: str, params: dict
    ) -> dict | None:
        """Fetch one page. Honors `Retry-After` on 429 and retries up to _MAX_RETRIES_ON_429."""
        for attempt in range(_MAX_RETRIES_ON_429 + 1):
            try:
                response = client.get(
                    url,
                    params=params,
                    headers={"X-API-KEY": self.api_key},
                )
            except httpx.RequestError as exc:
                logger.error(
                    "OpenStates request failed",
                    extra={
                        "event": "openstates_request_error",
                        "state": self.state_code,
                        "page": params.get("page"),
                        "error": str(exc),
                    },
                )
                return None

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:
                retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                logger.warning(
                    "OpenStates rate limit hit; backing off",
                    extra={
                        "event": "openstates_rate_limited",
                        "state": self.state_code,
                        "page": params.get("page"),
                        "attempt": attempt + 1,
                        "retry_after_seconds": retry_after,
                    },
                )
                if attempt < _MAX_RETRIES_ON_429:
                    time.sleep(retry_after)
                    continue
                return None

            logger.error(
                "OpenStates API returned an error status",
                extra={
                    "event": "openstates_api_error",
                    "state": self.state_code,
                    "page": params.get("page"),
                    "status_code": response.status_code,
                    "body": response.text[:300],
                },
            )
            return None
        return None

    def _upsert_bill(self, session: Session, bill: dict) -> bool:
        """Upsert a single OpenStates bill row. Returns True if newly added."""
        source_id = bill.get("id")
        title = (bill.get("title") or "").strip()
        if not source_id or not title:
            return False

        classification = bill.get("classification") or []
        type_name = classification[0] if classification else None

        bill_data = {
            "source": "openstates",
            "source_id": source_id,
            "city": self.city_key,
            "city_name": self.city_name,
            "state": self.state_code,
            "jurisdiction_level": "state",
            "file_number": bill.get("identifier"),
            "title": title,
            "type_name": type_name,
            "status": bill.get("latest_action_description"),
            "body_name": bill.get("from_organization", {}).get("name"),
            "intro_date": _parse_date(bill.get("first_action_date")),
            "agenda_date": None,
            "passed_date": None,
            "enactment_number": None,
            "enactment_date": None,
            "updated_at": _parse_datetime(bill.get("updated_at")),
            "url": bill.get("openstates_url"),
        }

        existing = (
            session.query(Bill)
            .filter_by(source="openstates", source_id=source_id, city=self.city_key)
            .first()
        )
        if existing:
            for key, value in bill_data.items():
                setattr(existing, key, value)
            return False
        session.add(Bill(**bill_data))
        return True
