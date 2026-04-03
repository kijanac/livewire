import json
import logging
import time
from datetime import datetime, timezone
from html.parser import HTMLParser

import httpx
from sqlalchemy.orm import Session

from app.briefing import call_openrouter
from app.config import settings
from app.models import Story
from app.tagger import VALID_TOPICS

logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "power_shift",
    "money_move",
    "movement_activity",
    "institutional",
    "crisis",
    "other",
]

TRIAGE_PROMPT = f"""You are an intelligence analyst for community organizers.

Given a batch of news headlines and descriptions from local media, classify each one.

For each story, return:
- "relevant": true if this story matters to community organizers (politics, policy, power, money, movements, civil rights, housing, labor, policing, public services). false for sports, entertainment, lifestyle, weather, obituaries, etc.
- "category": one of {json.dumps(VALID_CATEGORIES)}
  - power_shift: elections, appointments, resignations, caucus changes, recalls
  - money_move: budgets, contracts, development deals, bond measures
  - movement_activity: protests, strikes, campaigns, coalitions, community actions
  - institutional: court rulings, regulatory changes, executive orders, agency policy
  - crisis: incidents creating political urgency (police shootings, environmental disasters, housing emergencies)
  - other: relevant but doesn't fit above
- "topics": 1-3 topics from {json.dumps(VALID_TOPICS)}

Respond with a JSON object mapping each story ID to its classification.
Example: {{"1": {{"relevant": true, "category": "power_shift", "topics": ["elections"]}}, "2": {{"relevant": false, "category": null, "topics": []}}}}

Respond with ONLY the JSON object."""

ANALYSIS_PROMPT = """You are an intelligence analyst for community organizers.

Given a news article about political developments in {city_name}, {state}, write a 2-3 sentence analysis from an organizer's perspective. Focus on:
- Who benefits and who is affected
- What the power dynamics are
- What organizers should watch for or do next

Be direct and actionable. No preamble.

Headline: {title}

Article:
{body}"""

_MAX_HTML_BYTES = 2_000_000


# ---------------------------------------------------------------------------
# Stage 1: LLM triage — classify relevance, category, topics
# ---------------------------------------------------------------------------


def triage_stories(session: Session, batch_size: int = 15) -> int:
    """Classify a batch of unclassified stories. Returns count processed."""
    unclassified = (
        session.query(Story)
        .filter(Story.relevant.is_(None))
        .limit(batch_size)
        .all()
    )
    if not unclassified:
        return 0

    story_lines = []
    for s in unclassified:
        desc = (s.description or "")[:200]
        story_lines.append(f"ID {s.id}: {s.title}\n  {desc}")
    user_prompt = "Classify these stories:\n\n" + "\n\n".join(story_lines)

    story_map = {s.id: s for s in unclassified}

    try:
        raw = call_openrouter(
            user_prompt,
            system_prompt=TRIAGE_PROMPT,
            temperature=0.1,
            json_mode=True,
            timeout=60.0,
        )
        classifications = json.loads(raw)
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        logger.error(
            "Story triage API call failed",
            extra={"event": "story_triage_api_error", "error": str(exc)},
        )
        return 0
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.error(
            "Story triage parse failed",
            extra={"event": "story_triage_parse_error", "error": str(exc)},
        )
        # Mark as irrelevant to avoid infinite retries
        for story in unclassified:
            story.relevant = False
            story.classified_at = datetime.now(tz=timezone.utc)
        session.commit()
        return len(unclassified)

    now = datetime.now(tz=timezone.utc)
    classified = 0
    for story_id_str, result in classifications.items():
        try:
            story_id = int(story_id_str)
        except ValueError:
            continue

        story = story_map.get(story_id)
        if not story:
            continue

        story.relevant = bool(result.get("relevant", False))
        cat = result.get("category")
        story.category = cat if cat in VALID_CATEGORIES else None
        topics = [t for t in result.get("topics", []) if t in VALID_TOPICS]
        story.topics = json.dumps(topics) if topics else "[]"
        story.classified_at = now
        classified += 1

    # Mark any stories not in the response
    for story in unclassified:
        if story.relevant is None:
            story.relevant = False
            story.classified_at = now

    session.commit()
    logger.info(
        "Story triage batch completed",
        extra={"event": "story_triage_completed", "classified": classified},
    )
    return classified


def triage_all_stories(session: Session) -> int:
    """Triage all unclassified stories in batches."""
    if not settings.OPENROUTER_API_KEY:
        return 0

    total = 0
    while True:
        count = triage_stories(session, batch_size=15)
        if count == 0:
            break
        total += count
        time.sleep(0.5)

    logger.info(
        "Story triage completed",
        extra={"event": "story_triage_all_completed", "total": total},
    )
    return total


# ---------------------------------------------------------------------------
# Stage 2: deep fetch + organizer-lens analysis (relevant stories only)
# ---------------------------------------------------------------------------


class _ParagraphExtractor(HTMLParser):
    """Extract paragraph text from HTML, skipping script/style blocks."""

    def __init__(self) -> None:
        super().__init__()
        self._in_p = False
        self._in_script = False
        self.paragraphs: list[str] = []
        self._current = ""

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "p":
            self._in_p = True
            self._current = ""
        elif tag in ("script", "style"):
            self._in_script = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._in_p:
            self._in_p = False
            text = self._current.strip()
            if len(text) > 40:
                self.paragraphs.append(text)
        elif tag in ("script", "style"):
            self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_p and not self._in_script:
            self._current += data


def _fetch_article_body(url: str) -> str | None:
    """Fetch article text from URL. Returns body text or None."""
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Livewire/1.0)",
                },
            )
            response.raise_for_status()
            content_length = int(response.headers.get("content-length", 0))
            if content_length > _MAX_HTML_BYTES:
                return None
            html = response.text

        parser = _ParagraphExtractor()
        parser.feed(html)

        if not parser.paragraphs:
            return None

        body = "\n\n".join(parser.paragraphs)
        return body[:3000]

    except Exception as exc:
        logger.warning(
            "Article fetch failed",
            extra={
                "event": "article_fetch_failed",
                "url": url,
                "error": str(exc),
            },
        )
        return None


def enrich_stories(session: Session, batch_size: int = 10) -> int:
    """Fetch full content and generate analysis for relevant stories."""
    stories = (
        session.query(Story)
        .filter(Story.relevant.is_(True), Story.enriched_at.is_(None))
        .limit(batch_size)
        .all()
    )
    if not stories:
        return 0

    enriched = 0
    now = datetime.now(tz=timezone.utc)

    for story in stories:
        body = _fetch_article_body(story.source_url)
        if body:
            story.body = body

        content = body or story.description
        if content and settings.OPENROUTER_API_KEY:
            try:
                prompt = ANALYSIS_PROMPT.format(
                    city_name=story.city_name,
                    state=story.state,
                    title=story.title,
                    body=content,
                )
                story.analysis = call_openrouter(prompt)
            except Exception as exc:
                logger.warning(
                    "Story analysis generation failed",
                    extra={
                        "event": "story_analysis_failed",
                        "story_id": story.id,
                        "error": str(exc),
                    },
                )

        story.enriched_at = now
        enriched += 1
        time.sleep(0.3)

    session.commit()
    logger.info(
        "Story enrichment batch completed",
        extra={"event": "story_enrichment_completed", "enriched": enriched},
    )
    return enriched


def enrich_all_stories(session: Session) -> int:
    """Enrich all relevant unenriched stories in batches."""
    if not settings.OPENROUTER_API_KEY:
        return 0

    total = 0
    while True:
        count = enrich_stories(session, batch_size=10)
        if count == 0:
            break
        total += count

    logger.info(
        "Story enrichment completed",
        extra={"event": "story_enrichment_all_completed", "total": total},
    )
    return total
