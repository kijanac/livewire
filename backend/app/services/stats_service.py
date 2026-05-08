import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Bill, BillTopic
from app.schemas import (
    CityActivity,
    CityCount,
    StatsResponse,
    StatusCount,
    TopicCount,
)

_stats_cache: dict[str, tuple[StatsResponse, float]] = {}
_STATS_CACHE_TTL = 300


def build_stats(db: Session) -> StatsResponse:
    now_ts = time.time()
    if "__all__" in _stats_cache and (now_ts - _stats_cache["__all__"][1]) < _STATS_CACHE_TTL:
        return _stats_cache["__all__"][0]

    now = datetime.now(tz=timezone.utc)
    week_from_now = now + timedelta(days=7)
    week_ago = now - timedelta(days=7)

    moving_this_week = (
        db.query(func.count(Bill.id))
        .filter(Bill.agenda_date.isnot(None), Bill.agenda_date >= now, Bill.agenda_date <= week_from_now)
        .scalar()
    ) or 0

    new_bills_7d = (
        db.query(func.count(Bill.id))
        .filter(Bill.intro_date.isnot(None), Bill.intro_date >= week_ago)
        .scalar()
    ) or 0

    topic_rows = (
        db.query(BillTopic.topic_name, func.count(BillTopic.bill_id))
        .filter(BillTopic.topic_name != "other")
        .group_by(BillTopic.topic_name)
        .order_by(func.count(BillTopic.bill_id).desc())
        .limit(3)
        .all()
    )
    hot_topics = [TopicCount(topic=row[0], count=row[1]) for row in topic_rows]

    city_upcoming_rows = (
        db.query(Bill.city, Bill.city_name, func.count(Bill.id).label("cnt"))
        .filter(Bill.agenda_date.isnot(None), Bill.agenda_date >= now)
        .group_by(Bill.city, Bill.city_name)
        .order_by(func.count(Bill.id).desc())
        .first()
    )
    most_active_city = None
    if city_upcoming_rows:
        most_active_city = CityActivity(
            city=city_upcoming_rows[0],
            city_name=city_upcoming_rows[1],
            upcoming_count=city_upcoming_rows[2],
        )

    status_rows = (
        db.query(Bill.status, func.count(Bill.id).label("count"))
        .filter(Bill.status.isnot(None))
        .group_by(Bill.status)
        .order_by(func.count(Bill.id).desc())
        .limit(10)
        .all()
    )
    by_status = [StatusCount(status=row[0], count=row[1]) for row in status_rows]

    city_rows = (
        db.query(Bill.city, Bill.city_name, func.count(Bill.id).label("count"))
        .group_by(Bill.city, Bill.city_name)
        .order_by(func.count(Bill.id).desc())
        .all()
    )
    by_city = [
        CityCount(city=row[0], city_name=row[1], count=row[2]) for row in city_rows
    ]

    result = StatsResponse(
        moving_this_week=moving_this_week,
        hot_topics=hot_topics,
        most_active_city=most_active_city,
        new_bills_7d=new_bills_7d,
        by_status=by_status,
        by_city=by_city,
    )
    _stats_cache["__all__"] = (result, time.time())
    return result
