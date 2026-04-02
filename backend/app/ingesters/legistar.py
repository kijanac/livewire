import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.ingesters.base import BaseIngester
from app.models import Bill, BillAction, Official, VoteRecord, bill_sponsors

logger = logging.getLogger(__name__)

_YEA_VALUES = frozenset({"yea", "aye", "affirmative", "yes"})
_NAY_VALUES = frozenset({"nay", "no", "negative"})
_ABSTAIN_VALUES = frozenset({"abstain", "recused", "present"})
_ABSENT_VALUES = frozenset({"absent", "excused"})


def normalize_vote(raw: str) -> str:
    """Normalize a raw vote string to a canonical value."""
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

    def _fetch_list(self, client: httpx.Client, url: str) -> list | None:
        """Fetch a URL and return the parsed list, or None on failure."""
        try:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPStatusError, httpx.RequestError):
            return None
        if not isinstance(data, list):
            return None
        return data

    def _get_or_create_official(
        self, session: Session, source_id: str, name: str
    ) -> Official:
        """Look up an official by source_id+city, or create a stub."""
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

    def ingest_officials(self, session: Session) -> int:
        """Fetch persons (officials) from Legistar and upsert. Returns count of officials synced."""
        url = f"{self.base_url}/{self.city_key}/persons"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                persons = response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning(
                "Failed to fetch officials",
                extra={"event": "officials_fetch_failed", "city": self.city_key, "error": str(exc)},
            )
            return 0

        if not isinstance(persons, list):
            return 0

        count = 0
        for person in persons:
            source_id = str(person.get("PersonId", ""))
            name = person.get("PersonFullName", "")
            if not source_id or not name:
                continue

            existing = (
                session.query(Official)
                .filter_by(source_id=source_id, city=self.city_key)
                .first()
            )

            active_flag = person.get("PersonActiveFlag", 1)
            data = {
                "source_id": source_id,
                "city": self.city_key,
                "city_name": self.city_name,
                "state": self.state,
                "name": name,
                "title": person.get("PersonTitle"),
                "district": person.get("PersonWard"),
                "party": person.get("PersonParty"),
                "email": person.get("PersonEmail"),
                "website": person.get("PersonWWW"),
                "active": bool(active_flag),
                "updated_at": _parse_datetime(person.get("PersonLastModifiedUtc")),
            }

            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                session.add(Official(**data))
            count += 1

        session.commit()
        logger.info(
            "Officials ingestion completed",
            extra={"event": "officials_ingestion_completed", "city": self.city_key, "count": count},
        )
        return count

    def enrich_bill(self, session: Session, bill: Bill) -> dict:
        """On-demand: fetch sponsors, votes, and actions for a single bill.

        Returns dict with keys: sponsors, votes, actions (counts of records stored).
        """
        source_id = bill.source_id
        result = {"sponsors": 0, "votes": 0, "actions": 0}

        if bill.enriched_at:
            return result

        with httpx.Client(timeout=30.0) as client:
            result["sponsors"] = self._fetch_sponsors(client, session, bill, source_id)
            result["actions"] = self._fetch_actions(client, session, bill, source_id)
            result["votes"] = self._fetch_votes(client, session, bill, source_id)

        bill.enriched_at = datetime.now(tz=timezone.utc)
        session.commit()
        logger.info(
            "Bill enrichment completed",
            extra={
                "event": "bill_enrichment_completed",
                "bill_id": bill.id,
                "city": self.city_key,
                **result,
            },
        )
        return result

    def _fetch_sponsors(
        self, client: httpx.Client, session: Session, bill: Bill, source_id: str
    ) -> int:
        url = f"{self.base_url}/{self.city_key}/matters/{source_id}/sponsors"
        sponsors = self._fetch_list(client, url)
        if sponsors is None:
            return 0

        count = 0
        for sponsor in sponsors:
            person_id = str(sponsor.get("MatterSponsorNameId", ""))
            if not person_id:
                continue

            name = sponsor.get("MatterSponsorName", "Unknown")
            official = self._get_or_create_official(session, person_id, name)

            exists = session.execute(
                bill_sponsors.select().where(
                    bill_sponsors.c.bill_id == bill.id,
                    bill_sponsors.c.official_id == official.id,
                )
            ).first()
            if not exists:
                session.execute(
                    bill_sponsors.insert().values(bill_id=bill.id, official_id=official.id)
                )
                count += 1

        return count

    def _fetch_actions(
        self, client: httpx.Client, session: Session, bill: Bill, source_id: str
    ) -> int:
        url = f"{self.base_url}/{self.city_key}/matters/{source_id}/histories"
        actions = self._fetch_list(client, url)
        if actions is None:
            return 0

        count = 0
        for action in actions:
            action_text = action.get("MatterHistoryActionName", "")
            action_date = _parse_datetime(action.get("MatterHistoryActionDate"))
            body_name = action.get("MatterHistoryActionBodyName")
            result = action.get("MatterHistoryPassedFlagName")

            mover_id = None
            seconder_id = None
            mover_person_id = str(action.get("MatterHistoryMoverId") or "")
            seconder_person_id = str(action.get("MatterHistorySeconderId") or "")

            if mover_person_id and mover_person_id != "0":
                mover = session.query(Official).filter_by(
                    source_id=mover_person_id, city=self.city_key
                ).first()
                if mover:
                    mover_id = mover.id

            if seconder_person_id and seconder_person_id != "0":
                seconder = session.query(Official).filter_by(
                    source_id=seconder_person_id, city=self.city_key
                ).first()
                if seconder:
                    seconder_id = seconder.id

            session.add(BillAction(
                bill_id=bill.id,
                action_date=action_date,
                action_text=action_text,
                body_name=body_name,
                result=result,
                mover_id=mover_id,
                seconder_id=seconder_id,
            ))
            count += 1

        return count

    def _fetch_votes(
        self, client: httpx.Client, session: Session, bill: Bill, source_id: str
    ) -> int:
        url = f"{self.base_url}/{self.city_key}/matters/{source_id}/votes"
        votes = self._fetch_list(client, url)
        if votes is None:
            return 0

        count = 0
        for vote in votes:
            person_id = str(vote.get("VotePersonId", ""))
            if not person_id:
                continue

            name = vote.get("VotePersonName", "Unknown")
            official = self._get_or_create_official(session, person_id, name)

            vote_name = vote.get("VoteValueName", "")
            vote_value = normalize_vote(vote_name) if vote_name else "other"
            vote_date = _parse_datetime(vote.get("VoteLastModifiedUtc"))

            # Skip duplicates (same bill + official)
            existing = (
                session.query(VoteRecord)
                .filter_by(bill_id=bill.id, official_id=official.id)
                .first()
            )
            if existing:
                continue

            session.add(VoteRecord(
                bill_id=bill.id,
                official_id=official.id,
                vote_value=vote_value,
                vote_date=vote_date,
                action_text=vote.get("VoteEventItemActionName"),
            ))
            count += 1

        return count
