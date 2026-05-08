_PASSED_STATUSES = frozenset({
    "passed", "adopted", "approved", "enacted", "confirmed", "granted",
    "passed finally", "passed unsigned by mayor", "passed at full council",
    "adopted as amended", "granted (with modifications)",
})
_FAILED_STATUSES = frozenset({
    "failed", "denied", "dead", "disallowed", "withdrawn", "vetoed",
    "failed - end of term", "failed to pass",
    "died due to expiration of legislative council session",
})


def classify_outcome(status: str | None, passed_date: object) -> str:
    if passed_date:
        return "passed"
    s = (status or "").strip().lower()
    if s in _PASSED_STATUSES:
        return "passed"
    if s in _FAILED_STATUSES:
        return "failed"
    return "pending"
