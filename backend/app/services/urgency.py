from datetime import datetime, timezone

from app.models import Bill


def compute_urgency(bill: Bill) -> str:
    agenda_date = bill.agenda_date
    if not agenda_date:
        return "normal"
    now = datetime.now(tz=timezone.utc)
    if agenda_date.tzinfo is None:
        agenda_date = agenda_date.replace(tzinfo=timezone.utc)
    delta = (agenda_date - now).days
    if delta < 0:
        return "normal"
    if delta <= 7:
        return "urgent"
    if delta <= 30:
        return "soon"
    return "normal"
