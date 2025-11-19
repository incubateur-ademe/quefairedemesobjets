from datetime import datetime, timedelta, timezone

from stats.schemas import StatPeriodicity


def floor_to_period(date: datetime, periodicity: StatPeriodicity) -> datetime:
    """Floor the date to the beginning of the period."""
    if periodicity == "day":
        return date.replace(hour=0, minute=0, second=0, microsecond=0)
    if periodicity == "week":
        start = date - timedelta(days=date.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    if periodicity == "month":
        return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if periodicity == "year":
        return date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Périodicité inconnue : {periodicity}")


def shift_period(date: datetime, periodicity: StatPeriodicity, steps: int) -> datetime:
    """Shift the date by the given number of periods."""
    base = floor_to_period(date, periodicity)
    if periodicity == "day":
        return base + timedelta(days=steps)
    if periodicity == "week":
        return base + timedelta(weeks=steps)
    if periodicity == "month":
        month = (base.month - 1) + steps
        year = base.year + month // 12
        month = month % 12 + 1
        return base.replace(year=year, month=month, day=1)
    if periodicity == "year":
        return base.replace(year=base.year + steps, month=1, day=1)
    raise ValueError(f"Périodicité inconnue : {periodicity}")


def parse_date(date_str: str) -> datetime:
    """
    Parse a date in the format YYYY-MM-DD and return the beginning of the day in UTC.
    """
    if not date_str:
        raise ValueError("Date PostHog vide.")
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Date PostHog invalide: {date_str}") from exc
    return parsed.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
