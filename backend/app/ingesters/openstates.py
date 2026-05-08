import logging
import time
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx
from pydantic import BaseModel, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.config import settings
from app.ingesters.base import BaseIngester
from app.models import Bill

logger = logging.getLogger(__name__)

_DEFAULT_RETRY_AFTER_SECONDS = 60.0


# ---------------------------------------------------------------------------
# Field-level parsers
# ---------------------------------------------------------------------------

def _parse_retry_after(value: str | None) -> float:
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
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# API payload models
# ---------------------------------------------------------------------------

class OpenStatesBillPayload(BaseModel):
    """Single OpenStates bill from the v3 API. Use model_validate(raw_dict)."""

    model_config = {"extra": "ignore"}

    id: str
    title: str
    identifier: str | None = None
    classification: list[str] = []
    latest_action_description: str | None = None
    from_organization_name: str | None = None
    first_action_date: date | None = None
    updated_at: datetime | None = None
    openstates_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        # Pull nested from_organization.name flat
        org = data.pop("from_organization", None) or {}
        data["from_organization_name"] = org.get("name")
        # Strip whitespace from title
        if "title" in data and isinstance(data["title"], str):
            data["title"] = data["title"].strip()
        # Parse date strings
        data["first_action_date"] = _parse_date(data.get("first_action_date"))
        data["updated_at"] = _parse_datetime(data.get("updated_at"))
        return data

    @model_validator(mode="after")
    def _require_non_empty(self) -> "OpenStatesBillPayload":
        if not self.id or not self.title:
            raise ValueError("id and title must be non-empty")
        return self


class OpenStatesPage(BaseModel):
    """A page of OpenStates bill results + pagination."""

    results: list[OpenStatesBillPayload]
    max_page: int

    @classmethod
    def model_validate(cls, raw: object) -> "OpenStatesPage":  # type: ignore[override]
        if not isinstance(raw, dict):
            raise ValueError("expected dict")
        pagination = raw.get("pagination") or {}
        raw_results = raw.get("results") or []
        bills: list[OpenStatesBillPayload] = []
        for item in raw_results:
            if isinstance(item, dict):
                try:
                    bills.append(OpenStatesBillPayload.model_validate(item))
                except ValidationError:
                    pass  # skip malformed bills
        return cls(results=bills, max_page=pagination.get("max_page", 1))


# ---------------------------------------------------------------------------
# Ingester
# ---------------------------------------------------------------------------

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
        added = 0
        updated = 0

        if not self.api_key:
            logger.warning(
                "openstates_no_api_key",
                extra={"state": self.state_code},
            )
            return added, updated

        cutoff = (
            datetime.now(tz=timezone.utc)
            - timedelta(days=settings.OPENSTATES_LOOKBACK_DAYS)
        ).strftime("%Y-%m-%d")
        url = f"{self.base_url}/bills"

        logger.info(
            "openstates_ingestion_started",
            extra={
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
                    "per_page": settings.OPENSTATES_PER_PAGE,
                }
                api_page = self._fetch_page(client, url, params)
                if api_page is None:
                    break

                for bill in api_page.results:
                    if self._upsert_bill(session, bill):
                        added += 1
                    else:
                        updated += 1
                    total_seen += 1

                session.commit()

                if page >= api_page.max_page:
                    break
                page += 1

        logger.info(
            "openstates_ingestion_completed",
            extra={
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
    ) -> OpenStatesPage | None:
        max_attempts = 5
        backoff_base = 1.5
        retryable_5xx = {500, 502, 503, 504}

        for attempt in range(1, max_attempts + 1):
            try:
                response = client.get(
                    url,
                    params=params,
                    headers={"X-API-KEY": self.api_key},
                )
            except httpx.RequestError as exc:
                logger.error(
                    "openstates_request_error",
                    extra={
                        "state": self.state_code,
                        "page": params.get("page"),
                        "error": str(exc),
                    },
                )
                return None

            if response.status_code == 200:
                try:
                    return OpenStatesPage.model_validate(response.json())
                except (ValidationError, ValueError, TypeError):
                    logger.error(
                        "openstates_parse_error",
                        extra={
                            "state": self.state_code,
                            "page": params.get("page"),
                        },
                    )
                    return None

            if response.status_code == 429:
                retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                logger.warning(
                    "openstates_rate_limited",
                    extra={
                        "state": self.state_code,
                        "page": params.get("page"),
                        "attempt": attempt,
                        "retry_after_seconds": retry_after,
                    },
                )
                if attempt < max_attempts:
                    time.sleep(retry_after)
                    continue
                return None

            if response.status_code in retryable_5xx and attempt < max_attempts:
                wait_seconds = backoff_base ** attempt
                time.sleep(wait_seconds)
                continue

            logger.error(
                "openstates_api_error",
                extra={
                    "state": self.state_code,
                    "page": params.get("page"),
                    "status_code": response.status_code,
                    "body": response.text[:200],
                },
            )
            return None
        return None

    def _upsert_bill(self, session: Session, bill: OpenStatesBillPayload) -> bool:
        type_name = bill.classification[0] if bill.classification else None

        bill_data = {
            "source": "openstates",
            "source_id": bill.id,
            "city": self.city_key,
            "city_name": self.city_name,
            "state": self.state_code,
            "jurisdiction_level": "state",
            "file_number": bill.identifier,
            "title": bill.title,
            "type_name": type_name,
            "status": bill.latest_action_description,
            "body_name": bill.from_organization_name,
            "intro_date": bill.first_action_date,
            "agenda_date": None,
            "passed_date": None,
            "enactment_number": None,
            "enactment_date": None,
            "updated_at": bill.updated_at,
            "url": bill.openstates_url,
        }

        existing = (
            session.query(Bill)
            .filter_by(source="openstates", source_id=bill.id, city=self.city_key)
            .first()
        )
        if existing:
            for key, value in bill_data.items():
                setattr(existing, key, value)
            return False
        session.add(Bill(**bill_data))
        return True
