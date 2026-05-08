from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.models import Bill, BillTopic


@dataclass
class BillFilters:
    city: str | None = None
    status: str | None = None
    type_name: str | None = None
    topic: str | None = None
    urgency: str | None = None
    search: str | None = None
    jurisdiction_level: str | None = None
    page: int = 1
    per_page: int = 50


def query_bills(db: Session, filters: BillFilters) -> tuple[list[Bill], int]:
    query = db.query(Bill)

    if filters.city:
        query = query.filter(Bill.city == filters.city)
    if filters.status:
        query = query.filter(Bill.status == filters.status)
    if filters.type_name:
        query = query.filter(Bill.type_name == filters.type_name)
    if filters.jurisdiction_level:
        query = query.filter(Bill.jurisdiction_level == filters.jurisdiction_level)
    if filters.topic:
        query = query.join(BillTopic, BillTopic.bill_id == Bill.id).filter(
            BillTopic.topic_name == filters.topic,
        )
    if filters.search:
        query = query.filter(Bill.title.ilike(f"%{filters.search}%"))

    if filters.urgency == "urgent":
        now = datetime.now(tz=timezone.utc)
        cutoff = now + timedelta(days=7)
        query = query.filter(
            Bill.agenda_date.isnot(None),
            Bill.agenda_date >= now,
            Bill.agenda_date <= cutoff,
        )
    elif filters.urgency == "soon":
        now = datetime.now(tz=timezone.utc)
        cutoff_7 = now + timedelta(days=7)
        cutoff_30 = now + timedelta(days=30)
        query = query.filter(
            Bill.agenda_date.isnot(None),
            Bill.agenda_date > cutoff_7,
            Bill.agenda_date <= cutoff_30,
        )

    total = query.count()

    query = query.order_by(
        case((Bill.intro_date.is_(None), 1), else_=0),
        Bill.intro_date.desc(),
        Bill.updated_at.desc(),
    )

    offset = (filters.page - 1) * filters.per_page
    bills = query.offset(offset).limit(filters.per_page).all()

    return bills, total
