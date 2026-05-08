"""
HTML-fallback Legistar ingester for cities where the web API is not enabled.

Uses python-legistar-scraper (BSD-3) to scrape the Legistar web portal
directly via ASP.NET form submissions and HTML parsing.

Only invoked when the API-based LegistarIngester fails with a 500 error
(i.e., the city has Legistar but hasn't enabled the web API).
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Bill

logger = logging.getLogger(__name__)


class HTMLLegistarIngester:
    """Scrape bills from a Legistar web portal when the API is unavailable."""

    def __init__(self, city_key: str, city_config: dict) -> None:
        self.city_key = city_key
        self.city_name = city_config["name"]
        self.state = city_config["state"]
        self.base_url = f"https://{city_key}.legistar.com"

    def ingest(self, session: Session) -> tuple[int, int]:
        """Scrape bills from the HTML portal and upsert into the database."""
        from legistar.bills import LegistarBillScraper

        added = 0
        updated = 0

        # Build a city-specific scraper subclass
        scraper_cls = type(
            f"_{self.city_key.title()}BillScraper",
            (LegistarBillScraper,),
            {
                "BASE_URL": self.base_url,
                "LEGISLATION_URL": f"{self.base_url}/Legislation.aspx",
                "TIMEZONE": "America/Chicago",  # conservative default
            },
        )

        # 90-day lookback
        since = (datetime.now(timezone.utc) - timedelta(days=90)).replace(
            tzinfo=None
        )

        try:
            scraper = scraper_cls(requests_per_minute=30)
        except Exception as exc:
            logger.error(
                "html_ingester_init_failed",
                extra={"city": self.city_key, "error": str(exc)[:200]},
            )
            return added, updated

        logger.info(
            "html_ingestion_started",
            extra={"city": self.city_key, "city_name": self.city_name},
        )

        bill_count = 0
        try:
            for summary in scraper.legislation(created_after=since):
                bill_count += 1

                source_id = summary.get("Record #") or summary.get("File #") or ""
                title = summary.get("Title") or summary.get("Name") or ""
                if not source_id or not title:
                    continue

                file_number = summary.get("File #") or None
                status = summary.get("Status") or None
                type_name = summary.get("Type") or None
                intro_date = self._parse_date(summary.get("Introduction Date"))
                passed_date = self._parse_date(summary.get("Passed Date"))
                body_name = summary.get("Body") or None

                bill_data = {
                    "source": "legistar",
                    "source_id": str(source_id),
                    "city": self.city_key,
                    "city_name": self.city_name,
                    "state": self.state,
                    "file_number": file_number,
                    "title": title,
                    "type_name": type_name,
                    "status": status,
                    "body_name": body_name,
                    "intro_date": intro_date,
                    "agenda_date": None,
                    "passed_date": passed_date,
                    "enactment_number": None,
                    "enactment_date": None,
                    "url": summary.get(
                        "url",
                        f"{self.base_url}/gateway.aspx?m=l&id={source_id}",
                    ),
                    "updated_at": datetime.now(tz=timezone.utc),
                }

                existing = (
                    session.query(Bill)
                    .filter_by(
                        source="legistar",
                        source_id=str(source_id),
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

                # Commit in batches to avoid huge transactions
                if bill_count % 50 == 0:
                    session.commit()

        except Exception as exc:
            logger.exception(
                "html_ingestion_error",
                extra={"city": self.city_key, "error": str(exc)[:200]},
            )
        finally:
            session.commit()

        logger.info(
            "html_ingestion_completed",
            extra={
                "city": self.city_key,
                "city_name": self.city_name,
                "bills_added": added,
                "bills_updated": updated,
                "total_attempted": bill_count,
            },
        )

        return added, updated

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        """Parse M/D/YYYY format from Legistar HTML tables."""
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), "%m/%d/%Y")
        except (ValueError, TypeError):
            return None
