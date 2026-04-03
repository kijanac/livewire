import logging
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
                "RSS ingestion completed",
                extra={
                    "event": "rss_ingestion_completed",
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
            logger.error(
                "RSS ingestion failed",
                extra={
                    "event": "rss_ingestion_failed",
                    "source": self.source.name,
                    "city": self.source.city,
                    "error": str(exc),
                },
            )

        return added, 0

    def _fetch_feed(self) -> feedparser.FeedParserDict | None:
        """Fetch and parse the RSS feed."""
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
                    "Feed parse warning",
                    extra={
                        "event": "rss_parse_warning",
                        "source": self.source.name,
                        "error": str(feed.bozo_exception),
                    },
                )
            return feed
        except httpx.HTTPError as exc:
            logger.error(
                "Feed fetch failed",
                extra={
                    "event": "rss_fetch_failed",
                    "source": self.source.name,
                    "url": self.source.feed_url,
                    "error": str(exc),
                },
            )
            return None
