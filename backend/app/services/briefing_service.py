import json
import logging
from collections import defaultdict

import httpx
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.ingesters.legistar import LegistarIngester
from app.llm import call_openrouter
from app.models import Bill, BillAction, BillBriefing, Official, VoteRecord, bill_sponsors
from app.schemas import (
    ActionResponse,
    NarrativeSection,
    NewsArticle,
    NewsFrame,
    OfficialResponse,
    OfficialVotingPattern,
    PowerSection,
    VoteRecordResponse,
    VoteSummary,
    VotingPatterns,
)

logger = logging.getLogger(__name__)

_PATTERN_SIMILARITY_THRESHOLD = 0.5
_PATTERN_MAX_SIMILAR = 10
_SWING_LOW = 30.0
_SWING_HIGH = 70.0


def _build_voting_patterns(
    db: Session,
    current_vote_records: list[VoteRecord],
    similar_ids_scores: list[tuple[int, float]],
) -> VotingPatterns | None:
    official_ids = {
        vr.official_id for vr in current_vote_records if vr.official_id
    }
    if not official_ids:
        return None

    similar_bill_ids = [
        bid for bid, score in similar_ids_scores if score >= _PATTERN_SIMILARITY_THRESHOLD
    ]
    if not similar_bill_ids:
        return None

    history = (
        db.query(VoteRecord)
        .options(selectinload(VoteRecord.official))
        .filter(
            VoteRecord.bill_id.in_(similar_bill_ids),
            VoteRecord.official_id.in_(official_ids),
        )
        .all()
    )

    if not history:
        return None

    agg: dict[int, dict] = defaultdict(lambda: {"name": "", "district": None, "yea": 0, "nay": 0})
    for vr in history:
        entry = agg[vr.official_id]
        if vr.official:
            entry["name"] = vr.official.name
            entry["district"] = vr.official.district
        if vr.vote_value == "yea":
            entry["yea"] += 1
        elif vr.vote_value == "nay":
            entry["nay"] += 1

    patterns = []
    swing_voters = []
    for oid, data in agg.items():
        total = data["yea"] + data["nay"]
        if total == 0:
            continue
        pct = round((data["yea"] / total) * 100, 1)
        is_swing = _SWING_LOW <= pct <= _SWING_HIGH
        if is_swing:
            swing_voters.append(data["name"])
        patterns.append(OfficialVotingPattern(
            official_id=oid,
            name=data["name"],
            district=data["district"],
            alignment_pct=pct,
            yea=data["yea"],
            nay=data["nay"],
            total=total,
            is_swing=is_swing,
        ))

    if not patterns:
        return None

    patterns.sort(key=lambda p: p.alignment_pct, reverse=True)

    return VotingPatterns(
        patterns=patterns,
        similar_bill_count=len(similar_bill_ids),
        swing_voters=swing_voters,
    )


def _generate_power_analysis(
    bill: Bill,
    sponsors: list[OfficialResponse],
    votes: VoteSummary | None,
    actions: list[ActionResponse],
    voting_patterns: VotingPatterns | None = None,
) -> str:
    sponsor_text = ", ".join(s.name for s in sponsors) if sponsors else "No sponsors listed"
    vote_text = "No votes recorded"
    if votes:
        vote_text = f"Yea: {votes.yea}, Nay: {votes.nay}, Abstain: {votes.abstain}, Absent: {votes.absent}"
        if votes.records:
            nay_names = [r.official for r in votes.records if r.vote == "nay"]
            if nay_names:
                vote_text += f". Voted no: {', '.join(nay_names)}"

    action_text = "No action history"
    if actions:
        recent = actions[-5:]
        action_text = "; ".join(
            f"{a.date or '?'}: {a.action or '?'} ({a.body or '?'})" + (f" — {a.result}" if a.result else "")
            for a in recent
        )

    pattern_text = "No voting history on similar bills."
    if voting_patterns and voting_patterns.patterns:
        lines = []
        for p in voting_patterns.patterns:
            label = f"{p.name}: {p.alignment_pct}% alignment ({p.yea} yea, {p.nay} nay on {p.total} similar bills)"
            if p.is_swing:
                label += " — SWING VOTE"
            lines.append(label)
        pattern_text = (
            f"Voting history on {voting_patterns.similar_bill_count} similar bills:\n"
            + "\n".join(lines)
        )
        if voting_patterns.swing_voters:
            pattern_text += f"\nSwing voters: {', '.join(voting_patterns.swing_voters)}"

    prompt = (
        "You are a political intelligence analyst for community organizers. "
        "Given the following data about a legislative bill, write a 2-4 sentence power analysis. "
        "Focus on: who controls this bill's fate, any notable voting patterns "
        "(especially swing voters), and strategic observations an organizer should know. "
        "Be direct and actionable, not speculative.\n\n"
        f"Bill: {bill.title}\n"
        f"City: {bill.city_name}, {bill.state}\n"
        f"Status: {bill.status or 'Unknown'}\n"
        f"Committee/Body: {bill.body_name or 'Unknown'}\n"
        f"Sponsors: {sponsor_text}\n"
        f"Vote tally: {vote_text}\n"
        f"Recent actions: {action_text}\n"
        f"Historical voting patterns: {pattern_text}\n\n"
        "Write ONLY the analysis paragraph, no headers or formatting."
    )

    try:
        return call_openrouter(prompt, temperature=0.3, max_tokens=300).strip()
    except httpx.HTTPError as exc:
        logger.exception(
            "power_analysis_failed",
            extra={"bill_id": bill.id, "error": str(exc)[:200]},
        )
        return ""


def build_power_section(
    db: Session, bill: Bill, briefing: BillBriefing, similar_ids_scores: list[tuple[int, float]],
) -> PowerSection:
    city_config = settings.CITIES.get(bill.city)
    if city_config and not bill.enriched_at:
        ingester = LegistarIngester(
            city_key=bill.city,
            city_config=city_config,
            base_url=settings.LEGISTAR_BASE_URL,
        )
        ingester.enrich_bill(db, bill)

    sponsor_rows = (
        db.query(Official)
        .join(bill_sponsors, bill_sponsors.c.official_id == Official.id)
        .filter(bill_sponsors.c.bill_id == bill.id)
        .all()
    )
    sponsors = [OfficialResponse.model_validate(o) for o in sponsor_rows]

    vote_records = (
        db.query(VoteRecord)
        .options(selectinload(VoteRecord.official))
        .filter(VoteRecord.bill_id == bill.id)
        .all()
    )
    votes = None
    if vote_records:
        counts = {"yea": 0, "nay": 0, "abstain": 0, "absent": 0, "other": 0}
        records = []
        for vr in vote_records:
            counts[vr.vote_value] = counts.get(vr.vote_value, 0) + 1
            records.append(VoteRecordResponse(
                official=vr.official.name if vr.official else "Unknown",
                vote=vr.vote_value or "",
                district=vr.official.district if vr.official else None,
            ))
        votes = VoteSummary(**counts, records=records)

    action_rows = (
        db.query(BillAction)
        .options(selectinload(BillAction.mover), selectinload(BillAction.seconder))
        .filter(BillAction.bill_id == bill.id)
        .order_by(BillAction.action_date.asc())
        .all()
    )
    actions = [
        ActionResponse(
            date=a.action_date.isoformat() if a.action_date else None,
            action=a.action_text,
            body=a.body_name,
            result=a.result,
            mover=a.mover.name if a.mover else None,
            seconder=a.seconder.name if a.seconder else None,
        )
        for a in action_rows
    ]

    voting_patterns = _build_voting_patterns(db, vote_records, similar_ids_scores)

    analysis = briefing.power_analysis
    if not analysis and (sponsors or vote_records or action_rows) and settings.OPENROUTER_API_KEY:
        analysis = _generate_power_analysis(bill, sponsors, votes, actions, voting_patterns)
        briefing.power_analysis = analysis
        db.commit()

    return PowerSection(
        sponsors=sponsors,
        votes=votes,
        actions=actions,
        analysis=analysis,
        voting_patterns=voting_patterns,
    )


def _generate_narrative_analysis(
    bill: Bill, news: list[NewsArticle], actions: list[ActionResponse],
) -> NarrativeSection | None:
    headlines = "\n".join(
        f"- \"{a.title}\" ({a.source}, {a.date or 'undated'})"
        for a in news
    ) if news else "No news coverage found."

    action_text = "\n".join(
        f"- {a.date or '?'}: {a.action or '?'} ({a.body or '?'})"
        + (f" — Result: {a.result}" if a.result else "")
        for a in actions[-10:]
    ) if actions else "No action history."

    prompt = (
        "You are a narrative intelligence analyst for community organizers. "
        "Analyze how this bill is being framed in news coverage and official proceedings.\n\n"
        f"Bill: {bill.title}\n"
        f"City: {bill.city_name}, {bill.state}\n"
        f"Status: {bill.status or 'Unknown'}\n"
        f"Topics: {bill.topics or '[]'}\n\n"
        f"News Headlines:\n{headlines}\n\n"
        f"Recent Legislative Actions:\n{action_text}\n\n"
        "Return JSON with this structure:\n"
        "{\n"
        '  "frames": [{"source": "outlet name", "headline": "headline text", '
        '"frame": "2-4 word frame label", "stance": "support|opposition|neutral"}],\n'
        '  "support_narrative": "1-2 sentences: how supporters frame this",\n'
        '  "opposition_narrative": "1-2 sentences: how opponents frame this (or null if no opposition visible)",\n'
        '  "narrative_trajectory": "1 sentence: is the discourse shifting? In what direction?",\n'
        '  "talking_points": ["point 1", "point 2", "point 3"]\n'
        "}\n\n"
        "For frames, classify EACH news headline. For talking_points, suggest 2-3 concise "
        "points an organizer could use at a council meeting or in a flyer. Be direct."
    )

    try:
        raw = call_openrouter(
            prompt, temperature=0.3, response_format={"type": "json_object"},
        )
        parsed = json.loads(raw)

        frames = [
            NewsFrame(
                source=f.get("source", ""),
                headline=f.get("headline", ""),
                frame=f.get("frame", ""),
                stance=f.get("stance", "neutral"),
            )
            for f in parsed.get("frames", [])
            if isinstance(f, dict)
        ]

        return NarrativeSection(
            frames=frames,
            support_narrative=parsed.get("support_narrative"),
            opposition_narrative=parsed.get("opposition_narrative"),
            narrative_trajectory=parsed.get("narrative_trajectory"),
            talking_points=parsed.get("talking_points", []),
        )
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
        logger.exception(
            "narrative_analysis_failed",
            extra={"bill_id": bill.id, "error": str(exc)[:200]},
        )
        return None


def build_narrative_section(
    db: Session, bill: Bill, briefing: BillBriefing, news: list[NewsArticle], actions: list[ActionResponse],
) -> NarrativeSection | None:
    if not news and not actions:
        return None

    if briefing.narrative_json:
        try:
            cached = json.loads(briefing.narrative_json)
            return NarrativeSection(**cached)
        except (ValueError, TypeError):
            pass

    if not settings.OPENROUTER_API_KEY:
        return None

    analysis = _generate_narrative_analysis(bill, news, actions)
    if not analysis:
        return None

    briefing.narrative_json = json.dumps(analysis.model_dump())
    db.commit()

    return analysis
