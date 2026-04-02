import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class BillResponse(BaseModel):
    id: int
    source_id: str
    source: str
    city: str
    city_name: str
    state: str
    file_number: str | None = None
    title: str
    type_name: str | None = None
    status: str | None = None
    body_name: str | None = None
    intro_date: datetime | None = None
    agenda_date: datetime | None = None
    passed_date: datetime | None = None
    enactment_number: str | None = None
    enactment_date: datetime | None = None
    url: str | None = None
    topics: list[str] = []
    urgency: str = "normal"
    summary: str | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("topics", mode="before")
    @classmethod
    def parse_topics(cls, v: object) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        if v is None:
            return []
        return v  # type: ignore[return-value]


class BillListResponse(BaseModel):
    bills: list[BillResponse]
    total: int
    page: int
    per_page: int


class CityResponse(BaseModel):
    id: str
    name: str
    state: str


class StatusCount(BaseModel):
    status: str
    count: int


class CityCount(BaseModel):
    city: str
    city_name: str
    count: int


class TopicCount(BaseModel):
    topic: str
    count: int


class CityActivity(BaseModel):
    city: str
    city_name: str
    upcoming_count: int


class StatsResponse(BaseModel):
    moving_this_week: int
    hot_topics: list[TopicCount]
    most_active_city: CityActivity | None
    new_bills_7d: int
    by_status: list[StatusCount]
    by_city: list[CityCount]


class IngestRequest(BaseModel):
    city: str | None = None


class IngestResponse(BaseModel):
    message: str
    bills_added: int
    bills_updated: int


# --- Collection schemas ---


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None


class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CollectionItemAdd(BaseModel):
    bill_id: int
    note: str | None = None


class CollectionItemUpdate(BaseModel):
    note: str | None = None


class CollectionItemResponse(BaseModel):
    id: int
    bill_id: int
    bill: BillResponse
    note: str | None = None
    added_at: datetime | None = None

    model_config = {"from_attributes": True}


class CollectionResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None = None
    items: list[CollectionItemResponse] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CollectionSummaryResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None = None
    item_count: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Briefing schemas ---


class NewsArticle(BaseModel):
    title: str
    url: str
    source: str
    date: str | None = None


class SimilarBill(BaseModel):
    id: int
    city_name: str
    state: str
    title: str
    status: str | None = None
    file_number: str | None = None


class RadarBill(BaseModel):
    id: int
    city: str
    city_name: str
    state: str
    title: str
    file_number: str | None = None
    status: str | None = None
    type_name: str | None = None
    topics: list[str] = []
    urgency: str = "normal"
    intro_date: datetime | None = None
    url: str | None = None


class ClusterOutcomes(BaseModel):
    passed: int = 0
    failed: int = 0
    pending: int = 0
    avg_days_to_resolution: float | None = None
    earliest_intro: str | None = None
    latest_intro: str | None = None
    intro_span_days: int | None = None
    velocity_flag: bool = False
    insight: str | None = None


class RadarCluster(BaseModel):
    label: str
    top_terms: list[str]
    cities: list[str]
    city_count: int
    bill_count: int
    bills: list[RadarBill]
    outcomes: ClusterOutcomes | None = None


class RadarResponse(BaseModel):
    clusters: list[RadarCluster]
    total_clusters: int
    total_bills: int


# --- Power Intelligence schemas ---


class OfficialResponse(BaseModel):
    id: int
    name: str
    title: str | None = None
    district: str | None = None
    party: str | None = None
    body_name: str | None = None

    model_config = {"from_attributes": True}


class VoteRecordResponse(BaseModel):
    official: str
    vote: str
    district: str | None = None


class VoteSummary(BaseModel):
    yea: int = 0
    nay: int = 0
    abstain: int = 0
    absent: int = 0
    other: int = 0
    records: list[VoteRecordResponse] = []


class ActionResponse(BaseModel):
    date: str | None = None
    action: str | None = None
    body: str | None = None
    result: str | None = None
    mover: str | None = None
    seconder: str | None = None


class PowerSection(BaseModel):
    sponsors: list[OfficialResponse] = []
    votes: VoteSummary | None = None
    actions: list[ActionResponse] = []
    analysis: str | None = None


# --- Coalition Intelligence schemas ---


class CityAlignment(BaseModel):
    city: str
    city_name: str
    passed: int = 0
    failed: int = 0
    pending: int = 0
    momentum: str = "stable"  # "advancing", "stalled", "stable"


class TopicCoalition(BaseModel):
    topic: str
    topic_label: str
    city_count: int
    bill_count: int
    total_passed: int
    total_failed: int
    total_pending: int
    momentum: str = "stable"  # "advancing", "stalled", "mixed"
    cities: list[CityAlignment] = []
    insight: str | None = None


class CoalitionsResponse(BaseModel):
    topics: list[TopicCoalition]
    total_topics: int


class CoalitionBrief(BaseModel):
    ally_cities: list[str] = []
    contested_cities: list[str] = []
    insight: str | None = None


# --- Narrative Intelligence schemas ---


class NewsFrame(BaseModel):
    source: str
    headline: str
    frame: str
    stance: str  # "support", "opposition", "neutral"


class NarrativeSection(BaseModel):
    frames: list[NewsFrame] = []
    support_narrative: str | None = None
    opposition_narrative: str | None = None
    narrative_trajectory: str | None = None
    talking_points: list[str] = []


class BillBriefingResponse(BaseModel):
    bill: BillResponse
    summary: str | None = None
    impact: str | None = None
    organizing: str | None = None
    reception: str | None = None
    news: list[NewsArticle] = []
    similar_bills: list[SimilarBill] = []
    timeline: list[dict] = []
    collection_notes: list[dict] = []
    power: PowerSection | None = None
    narrative: NarrativeSection | None = None
    coalition: CoalitionBrief | None = None
