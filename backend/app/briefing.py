import json
import logging
import xml.etree.ElementTree as ET
from html import unescape

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Bill, BillBriefing

logger = logging.getLogger(__name__)

BRIEFING_PROMPT = """You are a community organizing intelligence analyst. Given a legislative bill's details and related news headlines, write a comprehensive briefing for community organizers.

Provide FOUR sections in JSON format:
{{
  "summary": "2-3 sentence plain-language explanation of what this bill does. No jargon. A high schooler should understand it.",
  "impact": "2-3 sentences on why community organizers should care. Who does this affect? What changes for residents? What's the organizing opportunity?",
  "organizing": "Based on the news coverage, describe any known organizing activity around this bill or issue: protests, petitions, campaigns, coalitions, progressive organizations fighting for or against it, community meetings, public testimony, grassroots efforts. If the news doesn't mention specific organizing, note what types of organizations would likely be involved and what actions they might take. 2-4 sentences.",
  "reception": "Based on the news coverage, assess the public reception of this bill: Is there vocal support or opposition? What are the main arguments on each side? Is media coverage favorable, critical, or neutral? Are there any controversies? 2-4 sentences."
}}

Bill details:
- Title: {title}
- City: {city_name}, {state}
- Type: {type_name}
- Status: {status}
- Body: {body_name}
- File Number: {file_number}
- Topics: {topics}

Related news headlines:
{news_headlines}

Respond with ONLY the JSON object."""


def call_openrouter(
    prompt: str,
    *,
    system_prompt: str | None = None,
    temperature: float = 0.3,
    max_tokens: int | None = None,
    json_mode: bool = False,
    timeout: float = 45.0,
) -> str:
    """Call OpenRouter and return the raw content string."""
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: dict = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            settings.OPENROUTER_BASE_URL,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


def _call_llm(prompt: str) -> dict:
    """Call OpenRouter and parse JSON response."""
    return json.loads(call_openrouter(prompt, json_mode=True))


def generate_briefing_text(bill: Bill, news: list[dict]) -> dict:
    """Generate full briefing with news context. Returns dict with summary, impact, organizing, reception."""
    if not settings.OPENROUTER_API_KEY:
        return {"summary": "", "impact": "", "organizing": "", "reception": ""}

    news_headlines = "\n".join(
        f"- {a['title']} ({a.get('source', 'Unknown')})"
        for a in news
    ) if news else "- No relevant news articles found."

    prompt = BRIEFING_PROMPT.format(
        title=bill.title,
        city_name=bill.city_name,
        state=bill.state,
        type_name=bill.type_name or "N/A",
        status=bill.status or "N/A",
        body_name=bill.body_name or "N/A",
        file_number=bill.file_number or "N/A",
        topics=bill.topics or "[]",
        news_headlines=news_headlines,
    )

    try:
        parsed = _call_llm(prompt)
        return {
            "summary": parsed.get("summary", ""),
            "impact": parsed.get("impact", ""),
            "organizing": parsed.get("organizing", ""),
            "reception": parsed.get("reception", ""),
        }
    except Exception as exc:
        logger.error(
            "Briefing generation failed",
            extra={"event": "briefing_generation_failed", "bill_id": bill.id, "error": str(exc)},
        )
        return {"summary": "", "impact": "", "organizing": "", "reception": ""}


def fetch_news_articles(query: str, max_results: int = 8) -> list[dict]:
    """Fetch related news from Google News RSS. Returns list of {title, url, source, date}."""
    words = query.split()[:10]
    search_query = " ".join(words)

    rss_url = "https://news.google.com/rss/search"
    params = {"q": search_query, "hl": "en-US", "gl": "US", "ceid": "US:en"}

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(rss_url, params=params)
            response.raise_for_status()

        root = ET.fromstring(response.text)
        articles = []
        for item in root.findall(".//item")[:max_results]:
            title_el = item.find("title")
            link_el = item.find("link")
            source_el = item.find("source")
            pub_date_el = item.find("pubDate")

            if title_el is not None and link_el is not None:
                articles.append({
                    "title": unescape(title_el.text or ""),
                    "url": link_el.text or "",
                    "source": source_el.text if source_el is not None else "",
                    "date": pub_date_el.text if pub_date_el is not None else None,
                })

        logger.info(
            "News articles fetched",
            extra={"event": "news_fetched", "query": search_query, "count": len(articles)},
        )
        return articles

    except Exception as exc:
        logger.error(
            "News fetch failed",
            extra={"event": "news_fetch_failed", "query": search_query, "error": str(exc)},
        )
        return []


def _build_news_query(bill: Bill) -> str:
    """Use LLM to extract a short, focused news search query from the bill."""
    if not settings.OPENROUTER_API_KEY:
        words = bill.title.split()[:6]
        return f"{bill.city_name} {' '.join(words)}"

    prompt = (
        f"Extract a short Google News search query (3-6 words) from this bill title. "
        f"Focus on the core subject, not procedural language like 'approving' or 'authorizing'. "
        f"Include the city name. Return ONLY the search query text, nothing else.\n\n"
        f"City: {bill.city_name}\nTitle: {bill.title}"
    )

    try:
        query = call_openrouter(prompt, temperature=0.1, max_tokens=30).strip().strip('"')
        return query[:80]
    except Exception:
        words = bill.title.split()[:6]
        return f"{bill.city_name} {' '.join(words)}"


def get_or_create_briefing(session: Session, bill: Bill) -> BillBriefing:
    """Get cached briefing or generate a new one."""
    existing = session.query(BillBriefing).filter(BillBriefing.bill_id == bill.id).first()
    if existing:
        return existing

    # Build a focused news query, then fetch
    news_query = _build_news_query(bill)
    news = fetch_news_articles(news_query)

    briefing_text = generate_briefing_text(bill, news)

    briefing = BillBriefing(
        bill_id=bill.id,
        summary=briefing_text["summary"],
        impact=briefing_text["impact"],
        organizing=briefing_text["organizing"],
        reception=briefing_text["reception"],
        news_json=json.dumps(news),
    )
    session.add(briefing)
    session.commit()
    session.refresh(briefing)

    logger.info(
        "Briefing generated",
        extra={
            "event": "briefing_generated",
            "bill_id": bill.id,
            "has_summary": bool(briefing_text["summary"]),
            "news_count": len(news),
        },
    )
    return briefing
