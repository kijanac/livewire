import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Story, StorySource
from app.schemas import StoryListResponse, StoryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stories", tags=["stories"])


def _story_to_response(story: Story, source_name: str | None = None) -> StoryResponse:
    return StoryResponse(
        id=story.id,
        source_id=story.source_id,
        source_name=source_name,
        city=story.city,
        city_name=story.city_name,
        state=story.state,
        title=story.title,
        description=story.description,
        source_url=story.source_url,
        published_at=story.published_at,
        relevant=story.relevant,
        category=story.category,
        topics=story.topics,
        analysis=story.analysis,
        enriched_at=story.enriched_at,
        created_at=story.created_at,
    )


@router.get("", response_model=StoryListResponse)
def list_stories(
    city: str | None = Query(None),
    category: str | None = Query(None),
    topic: str | None = Query(None),
    relevant_only: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> StoryListResponse:
    query = db.query(Story, StorySource.name).join(
        StorySource, Story.source_id == StorySource.id
    )

    if relevant_only:
        query = query.filter(Story.relevant.is_(True))
    if city:
        query = query.filter(Story.city == city)
    if category:
        query = query.filter(Story.category == category)
    if topic:
        query = query.filter(Story.topics.like(f'%"{topic}"%'))

    total = query.count()

    rows = (
        query.order_by(Story.published_at.desc().nullslast())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    stories = [_story_to_response(story, source_name) for story, source_name in rows]

    return StoryListResponse(
        stories=stories,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{story_id}", response_model=StoryResponse)
def get_story(
    story_id: int,
    db: Session = Depends(get_db),
) -> StoryResponse:
    row = (
        db.query(Story, StorySource.name)
        .join(StorySource, Story.source_id == StorySource.id)
        .filter(Story.id == story_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Story not found")

    story, source_name = row
    return _story_to_response(story, source_name)
