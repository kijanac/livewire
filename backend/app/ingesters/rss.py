import logging
import time
from datetime import datetime, timezone

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.ingesters.base import BaseIngester
from app.models import Story, StorySource

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (compatible; Livewire/1.0; +https://github.com/livewire)"
)
_FETCH_MAX_ATTEMPTS = 3
_FETCH_BACKOFF_BASE = 2.0


def _parse_published(entry: dict) -> datetime | None:
    """Extract published datetime from an RSS entry."""
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, field, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


class RSSIngester(BaseIngester):
    """Fetch stories from an RSS feed and store new entries."""

    def __init__(self, source: StorySource) -> None:
        self.source = source

    def ingest(self, session: Session) -> tuple[int, int]:
        added = 0
        try:
            feed = self._fetch_feed()
            if feed is None:
                return 0, 0

            self.source.last_fetched = datetime.now(tz=timezone.utc)
            self.source.fetch_count += 1

            for entry in feed.entries:
                link = entry.get("link", "")
                if not link:
                    continue

                exists = (
                    session.query(Story.id)
                    .filter(Story.source_url == link)
                    .first()
                )
                if exists:
                    continue

                story = Story(
                    source_id=self.source.id,
                    city=self.source.city,
                    city_name=self.source.city_name,
                    state=self.source.state,
                    title=entry.get("title", "").strip(),
                    description=(entry.get("summary") or entry.get("description") or "").strip() or None,
                    source_url=link,
                    published_at=_parse_published(entry),
                )
                session.add(story)
                added += 1

            # Clear error state on success
            self.source.error_count = 0
            self.source.last_error = None
            session.commit()

            logger.info(
                "rss_ingestion_completed",
                extra={
                    "source": self.source.name,
                    "city": self.source.city,
                    "stories_added": added,
                },
            )
        except Exception as exc:
            session.rollback()
            self.source.error_count += 1
            self.source.last_error = str(exc)[:500]
            session.commit()
            logger.exception(
                "rss_ingestion_failed",
                extra={
                    "source": self.source.name,
                    "city": self.source.city,
                    "feed_url": self.source.feed_url,
                },
            )

        return added, 0

    def _fetch_feed(self) -> feedparser.FeedParserDict | None:
        """Fetch and parse the RSS feed. Retries transient errors with exponential backoff."""
        last_exc: httpx.RequestError | None = None
        for attempt in range(1, _FETCH_MAX_ATTEMPTS + 1):
            try:
                with httpx.Client(timeout=20.0) as client:
                    response = client.get(
                        self.source.feed_url,
                        headers={"User-Agent": _USER_AGENT},
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                feed = feedparser.parse(response.text)
                if feed.bozo:
                    logger.warning(
                        "rss_parse_warning",
                        extra={
                            "source": self.source.name,
                            "feed_url": self.source.feed_url,
                            "error": str(feed.bozo_exception)[:200],
                        },
                    )
                return feed
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt < _FETCH_MAX_ATTEMPTS:
                    wait_seconds = _FETCH_BACKOFF_BASE ** attempt
                    logger.warning(
                        "rss_feed_retried",
                        extra={
                            "attempt": attempt,
                            "feed_url": self.source.feed_url,
                            "source": self.source.name,
                            "wait_seconds": wait_seconds,
                            "error": str(exc)[:200],
                        },
                    )
                    time.sleep(wait_seconds)
                    continue
                logger.error(
                    "rss_fetch_failed",
                    extra={
                        "source": self.source.name,
                        "feed_url": self.source.feed_url,
                        "attempts": attempt,
                        "error": str(exc)[:200],
                    },
                )
                return None
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "rss_fetch_failed",
                    extra={
                        "source": self.source.name,
                        "feed_url": self.source.feed_url,
                        "status_code": exc.response.status_code,
                    },
                )
                return None

        if last_exc is not None:
            return None
        return None
