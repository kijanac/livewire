import logging
from datetime import datetime, timedelta, timezone
from typing import TypeVar

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from sqlalchemy.orm import Session

from app.ingesters.base import BaseIngester
from app.models import Bill, BillAction, BillDocument, Official, VoteRecord, bill_sponsors

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_YEA_VALUES = frozenset({"yea", "aye", "affirmative", "yes"})
_NAY_VALUES = frozenset({"nay", "no", "negative"})
_ABSTAIN_VALUES = frozenset({"abstain", "recused", "present"})
_ABSENT_VALUES = frozenset({"absent", "excused"})


def normalize_vote(raw: str) -> str:
    val = raw.strip().lower()
    if val in _YEA_VALUES:
        return "yea"
    if val in _NAY_VALUES:
        return "nay"
    if val in _ABSTAIN_VALUES:
        return "abstain"
    if val in _ABSENT_VALUES:
        return "absent"
    return "other"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# API payload models
# ---------------------------------------------------------------------------

class LegistarMatterPayload(BaseModel):
    """A Legistar matter from the API."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    source_id: str = Field(alias="MatterId")
    title: str = Field(alias="MatterTitle")
    file_number: str | None = Field(default=None, alias="MatterFile")
    type_name: str | None = Field(default=None, alias="MatterTypeName")
    status_name: str | None = Field(default=None, alias="MatterStatusName")
    body_name: str | None = Field(default=None, alias="MatterBodyName")
    intro_date: datetime | None = Field(default=None, alias="MatterIntroDate")
    agenda_date: datetime | None = Field(default=None, alias="MatterAgendaDate")
    passed_date: datetime | None = Field(default=None, alias="MatterPassedDate")
    enactment_number: str | None = Field(default=None, alias="MatterEnactmentNumber")
    enactment_date: datetime | None = Field(default=None, alias="MatterEnactmentDate")
    last_modified_utc: datetime | None = Field(default=None, alias="MatterLastModifiedUtc")

    @field_validator("source_id", mode="before")
    @classmethod
    def _coerce_str(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @field_validator("intro_date", "agenda_date", "passed_date",
                     "enactment_date", "last_modified_utc", mode="before")
    @classmethod
    def _coerce_datetime(cls, v: object) -> datetime | None:
        if v is None or v == "":
            return None
        return _parse_datetime(str(v))

    @model_validator(mode="before")
    @classmethod
    def _fallback_title(cls, data: object) -> object:
        """If MatterTitle is missing, fall back to MatterName."""
        if not isinstance(data, dict):
            return data
        if not data.get("MatterTitle") and data.get("MatterName"):
            data["MatterTitle"] = data["MatterName"]
        return data

    @model_validator(mode="after")
    def _require_non_empty(self) -> "LegistarMatterPayload":
        if not self.source_id or not self.title:
            raise ValueError("source_id and title must be non-empty")
        return self


class LegistarSponsorPayload(BaseModel):
    """A sponsor from the Legistar sponsors endpoint."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    person_id: str = Field(alias="MatterSponsorNameId")
    name: str = Field(default="Unknown", alias="MatterSponsorName")

    @field_validator("person_id", mode="before")
    @classmethod
    def _coerce_str(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @model_validator(mode="after")
    def _require_person_id(self) -> "LegistarSponsorPayload":
        if not self.person_id:
            raise ValueError("person_id must be non-empty")
        return self


class LegistarVotePayload(BaseModel):
    """A vote record from the Legistar votes endpoint."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    person_id: str = Field(alias="VotePersonId")
    name: str = Field(default="Unknown", alias="VotePersonName")
    vote_value: str = Field(alias="VoteValueName")
    vote_date: datetime | None = Field(default=None, alias="VoteLastModifiedUtc")
    action_text: str | None = Field(default=None, alias="VoteEventItemActionName")

    @field_validator("person_id", mode="before")
    @classmethod
    def _coerce_str(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @field_validator("vote_value", mode="before")
    @classmethod
    def _canonicalize_vote(cls, v: object) -> str:
        raw = str(v) if v else ""
        return normalize_vote(raw)

    @field_validator("vote_date", mode="before")
    @classmethod
    def _coerce_datetime(cls, v: object) -> datetime | None:
        if v is None or v == "":
            return None
        return _parse_datetime(str(v))

    @model_validator(mode="after")
    def _require_person_id(self) -> "LegistarVotePayload":
        if not self.person_id:
            raise ValueError("person_id must be non-empty")
        return self


class LegistarActionPayload(BaseModel):
    """An action/history entry with resolved Official IDs."""

    model_config = {"extra": "ignore"}

    action_text: str = ""
    action_date: datetime | None = None
    body_name: str | None = None
    result: str | None = None
    mover_id: int | None = None
    seconder_id: int | None = None

    @classmethod
    def from_history(
        cls,
        raw: dict,
        mover_id: int | None,
        seconder_id: int | None,
    ) -> "LegistarActionPayload":
        """Build from a raw history dict + resolved Official IDs."""
        return cls(
            action_text=raw.get("MatterHistoryActionName", ""),
            action_date=_parse_datetime(raw.get("MatterHistoryActionDate")),
            body_name=raw.get("MatterHistoryActionBodyName"),
            result=raw.get("MatterHistoryPassedFlagName"),
            mover_id=mover_id,
            seconder_id=seconder_id,
        )


class LegistarAttachmentPayload(BaseModel):
    """An attachment from the Legistar attachments endpoint."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    name: str = Field(alias="MatterAttachmentName")
    url: str = Field(alias="MatterAttachmentHyperlink")

    @model_validator(mode="after")
    def _require_fields(self) -> "LegistarAttachmentPayload":
        if not self.name or not self.url:
            raise ValueError("name and url must be non-empty")
        return self


class LegistarPersonPayload(BaseModel):
    """A person/official from the Legistar persons endpoint."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    source_id: str = Field(alias="PersonId")
    name: str = Field(alias="PersonFullName")
    title: str | None = Field(default=None, alias="PersonTitle")
    district: str | None = Field(default=None, alias="PersonWard")
    party: str | None = Field(default=None, alias="PersonParty")
    email: str | None = Field(default=None, alias="PersonEmail")
    website: str | None = Field(default=None, alias="PersonWWW")
    active: bool = Field(default=True, alias="PersonActiveFlag")
    updated_at: datetime | None = Field(default=None, alias="PersonLastModifiedUtc")

    @field_validator("source_id", mode="before")
    @classmethod
    def _coerce_str(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @field_validator("active", mode="before")
    @classmethod
    def _coerce_bool(cls, v: object) -> bool:
        if v is None:
            return True
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        return str(v).lower() in ("1", "true", "yes")

    @field_validator("updated_at", mode="before")
    @classmethod
    def _coerce_datetime(cls, v: object) -> datetime | None:
        if v is None or v == "":
            return None
        return _parse_datetime(str(v))

    @model_validator(mode="after")
    def _require_fields(self) -> "LegistarPersonPayload":
        if not self.source_id or not self.name:
            raise ValueError("source_id and name must be non-empty")
        return self


# ---------------------------------------------------------------------------
# Ingester
# ---------------------------------------------------------------------------

class LegistarIngester(BaseIngester):
    def __init__(self, city_key: str, city_config: dict, base_url: str) -> None:
        self.city_key = city_key
        self.city_name = city_config["name"]
        self.state = city_config["state"]
        self.base_url = base_url

    # ------------------------------------------------------------------
    # Boundary: fetch + parse related endpoints
    # ------------------------------------------------------------------

    def _fetch_related(
        self,
        client: httpx.Client,
        source_id: str,
        endpoint: str,
        model: type[T],
    ) -> list[T]:
        """Fetch a per-matter endpoint and parse each row at the boundary."""
        url = f"{self.base_url}/{self.city_key}/matters/{source_id}/{endpoint}"
        try:
            response = client.get(url)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "legistar_related_fetch_failed",
                extra={
                    "city": self.city_key,
                    "source_id": source_id,
                    "endpoint": endpoint,
                    "error": str(exc)[:200],
                },
            )
            return []

        if not isinstance(raw_data, list):
            return []

        parsed: list[T] = []
        for item in raw_data:
            if isinstance(item, dict):
                try:
                    parsed.append(model.model_validate(item))
                except ValidationError:
                    pass  # skip malformed rows
        return parsed

    def _resolve_official(self, session: Session, person_id: str) -> int | None:
        if not person_id or person_id == "0":
            return None
        official = (
            session.query(Official)
            .filter_by(source_id=person_id, city=self.city_key)
            .first()
        )
        return official.id if official else None

    def _get_or_create_official(
        self, session: Session, source_id: str, name: str
    ) -> Official:
        official = (
            session.query(Official)
            .filter_by(source_id=source_id, city=self.city_key)
            .first()
        )
        if not official:
            official = Official(
                source_id=source_id,
                city=self.city_key,
                city_name=self.city_name,
                state=self.state,
                name=name,
            )
            session.add(official)
            session.flush()
        return official

    # ------------------------------------------------------------------
    # Main ingestion
    # ------------------------------------------------------------------

    def ingest(self, session: Session) -> tuple[int, int]:
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
            "ingestion_started",
            extra={
                "city": self.city_key,
                "city_name": self.city_name,
                "endpoint": url,
            },
        )

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                raw_matters = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ingestion_api_error",
                extra={
                    "city": self.city_key,
                    "status_code": exc.response.status_code,
                    "endpoint": url,
                },
            )
            return added, updated
        except httpx.RequestError as exc:
            logger.error(
                "ingestion_request_error",
                extra={
                    "city": self.city_key,
                    "error": str(exc)[:200],
                    "endpoint": url,
                },
            )
            return added, updated

        if not isinstance(raw_matters, list):
            logger.warning(
                "ingestion_unexpected_response",
                extra={
                    "city": self.city_key,
                    "response_type": type(raw_matters).__name__,
                },
            )
            return added, updated

        matters: list[LegistarMatterPayload] = []
        for item in raw_matters:
            if isinstance(item, dict):
                try:
                    matters.append(LegistarMatterPayload.model_validate(item))
                except ValidationError:
                    pass  # skip malformed matters

        for matter in matters:
            bill_url = (
                f"https://{self.city_key}.legistar.com"
                f"/gateway.aspx?m=l&id={matter.source_id}"
            )

            bill_data = {
                "source": "legistar",
                "source_id": matter.source_id,
                "city": self.city_key,
                "city_name": self.city_name,
                "state": self.state,
                "file_number": matter.file_number,
                "title": matter.title,
                "type_name": matter.type_name,
                "status": matter.status_name,
                "body_name": matter.body_name,
                "intro_date": matter.intro_date,
                "agenda_date": matter.agenda_date,
                "passed_date": matter.passed_date,
                "enactment_number": matter.enactment_number,
                "enactment_date": matter.enactment_date,
                "updated_at": matter.last_modified_utc,
                "url": bill_url,
            }

            existing = (
                session.query(Bill)
                .filter_by(
                    source="legistar",
                    source_id=matter.source_id,
                    city=self.city_key,
                )
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
            "ingestion_completed",
            extra={
                "city": self.city_key,
                "city_name": self.city_name,
                "bills_added": added,
                "bills_updated": updated,
                "total_matters": len(matters),
            },
        )

        return added, updated

    def ingest_officials(self, session: Session) -> int:
        url = f"{self.base_url}/{self.city_key}/persons"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                raw_persons = response.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "officials_fetch_failed",
                extra={"city": self.city_key, "error": str(exc)[:200]},
            )
            return 0

        if not isinstance(raw_persons, list):
            return 0

        persons: list[LegistarPersonPayload] = []
        for item in raw_persons:
            if isinstance(item, dict):
                try:
                    persons.append(LegistarPersonPayload.model_validate(item))
                except ValidationError:
                    pass

        count = 0
        for person in persons:
            existing = (
                session.query(Official)
                .filter_by(source_id=person.source_id, city=self.city_key)
                .first()
            )

            data = {
                "source_id": person.source_id,
                "city": self.city_key,
                "city_name": self.city_name,
                "state": self.state,
                "name": person.name,
                "title": person.title,
                "district": person.district,
                "party": person.party,
                "email": person.email,
                "website": person.website,
                "active": person.active,
                "updated_at": person.updated_at,
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                session.add(Official(**data))
            count += 1

        session.commit()
        logger.info(
            "officials_ingestion_completed",
            extra={"city": self.city_key, "count": count},
        )
        return count

    def enrich_bill(self, session: Session, bill: Bill) -> dict:
        if bill.enriched_at:
            return {"sponsors": 0, "votes": 0, "actions": 0, "documents": 0}

        source_id = bill.source_id

        with httpx.Client(timeout=30.0) as client:
            sponsor_count = self._fetch_sponsors(client, session, bill, source_id)
            action_count = self._fetch_actions(client, session, bill, source_id)
            vote_count = self._fetch_votes(client, session, bill, source_id)
            doc_count = self._fetch_attachments(client, session, bill, source_id)

        bill.enriched_at = datetime.now(tz=timezone.utc)
        session.commit()
        logger.info(
            "bill_enrichment_completed",
            extra={
                "bill_id": bill.id,
                "city": self.city_key,
                "sponsors": sponsor_count,
                "actions": action_count,
                "votes": vote_count,
                "documents": doc_count,
            },
        )
        return {
            "sponsors": sponsor_count,
            "votes": vote_count,
            "actions": action_count,
            "documents": doc_count,
        }

    def _fetch_sponsors(
        self,
        client: httpx.Client,
        session: Session,
        bill: Bill,
        source_id: str,
    ) -> int:
        sponsors = self._fetch_related(
            client, source_id, "sponsors", LegistarSponsorPayload
        )
        count = 0
        for sponsor in sponsors:
            official = self._get_or_create_official(session, sponsor.person_id, sponsor.name)
            exists = session.execute(
                bill_sponsors.select().where(
                    bill_sponsors.c.bill_id == bill.id,
                    bill_sponsors.c.official_id == official.id,
                )
            ).first()
            if not exists:
                session.execute(
                    bill_sponsors.insert().values(
                        bill_id=bill.id, official_id=official.id
                    )
                )
                count += 1
        return count

    def _fetch_actions(
        self,
        client: httpx.Client,
        session: Session,
        bill: Bill,
        source_id: str,
    ) -> int:
        """Fetch action history. Actions need Official ID resolution, so we
        use from_history() instead of model_validate directly."""
        url = f"{self.base_url}/{self.city_key}/matters/{source_id}/histories"
        try:
            response = client.get(url)
            response.raise_for_status()
            raw_histories = response.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "legistar_related_fetch_failed",
                extra={
                    "city": self.city_key,
                    "source_id": source_id,
                    "endpoint": "histories",
                    "error": str(exc)[:200],
                },
            )
            return 0

        if not isinstance(raw_histories, list):
            return 0

        for item in raw_histories:
            if not isinstance(item, dict):
                continue
            mover_person_id = str(item.get("MatterHistoryMoverId") or "")
            seconder_person_id = str(item.get("MatterHistorySeconderId") or "")
            action = LegistarActionPayload.from_history(
                item,
                mover_id=self._resolve_official(session, mover_person_id),
                seconder_id=self._resolve_official(session, seconder_person_id),
            )
            session.add(
                BillAction(
                    bill_id=bill.id,
                    action_date=action.action_date,
                    action_text=action.action_text,
                    body_name=action.body_name,
                    result=action.result,
                    mover_id=action.mover_id,
                    seconder_id=action.seconder_id,
                )
            )
        return len(raw_histories)

    def _fetch_votes(
        self,
        client: httpx.Client,
        session: Session,
        bill: Bill,
        source_id: str,
    ) -> int:
        votes = self._fetch_related(
            client, source_id, "votes", LegistarVotePayload
        )
        count = 0
        for vote in votes:
            official = self._get_or_create_official(session, vote.person_id, vote.name)

            existing = (
                session.query(VoteRecord)
                .filter_by(bill_id=bill.id, official_id=official.id)
                .first()
            )
            if existing:
                continue

            session.add(
                VoteRecord(
                    bill_id=bill.id,
                    official_id=official.id,
                    vote_value=vote.vote_value,
                    vote_date=vote.vote_date,
                    action_text=vote.action_text,
                )
            )
            count += 1
        return count

    def _fetch_attachments(
        self,
        client: httpx.Client,
        session: Session,
        bill: Bill,
        source_id: str,
    ) -> int:
        attachments = self._fetch_related(
            client, source_id, "attachments", LegistarAttachmentPayload
        )
        count = 0
        for att in attachments:
            existing = (
                session.query(BillDocument)
                .filter_by(bill_id=bill.id, url=att.url)
                .first()
            )
            if existing:
                continue
            session.add(BillDocument(bill_id=bill.id, name=att.name, url=att.url))
            count += 1
        return count
