from datetime import time
from typing import Any, Dict, List, Tuple

from opening_hours import OpeningHours

OPENED_24_7 = {
    "Mo": [(time(0, 0), time(23, 59))],
    "Tu": [(time(0, 0), time(23, 59))],
    "We": [(time(0, 0), time(23, 59))],
    "Th": [(time(0, 0), time(23, 59))],
    "Fr": [(time(0, 0), time(23, 59))],
    "Sa": [(time(0, 0), time(23, 59))],
    "Su": [(time(0, 0), time(23, 59))],
}

DAYS_OF_WEEK = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def merge_consecutive_tuples(tuples: list[tuple[Any, Any]]) -> list[tuple[Any, Any]]:
    result = []
    if tuples:
        current_start, current_end = tuples[0]
        for next_start, next_end in tuples[1:]:
            if current_end == next_start:
                current_end = next_end
            else:
                result.append((current_start, current_end))
                current_start, current_end = next_start, next_end
        result.append((current_start, current_end))
    return result


def split_and_clean(value: str) -> List[str]:
    """
    Divise une chaîne par ', ' ou '; ' et nettoie chaque valeur.
    """
    parts = []
    for part in value.split("; "):
        parts.extend(part.split(", "))
    return [part.strip() for part in parts if part.strip()]


def interprete_opening_hours(opening_hours: str | None):
    """
    Interprete les heures d'ouverture d'un lieu.
    """

    if not opening_hours:
        return {}

    opening_hours_normalized = str(OpeningHours(opening_hours).normalize())

    if opening_hours_normalized == "24/7":
        return OPENED_24_7

    opening_hours_by_day_of_week: Dict[str, List[Tuple[time, time]]] = {
        day: [] for day in DAYS_OF_WEEK
    }

    def get_opening_hours(hours: str):
        hours_list = hours.split(",")
        result_hours = []
        for hour in hours_list:
            open, close = hour.split("-")
            open_hour, open_minute = map(int, open.split(":"))
            close_hour, close_minute = map(int, close.split(":"))
            result_hours.append(
                (time(open_hour, open_minute), time(close_hour, close_minute))
            )
        return result_hours

    def get_opening_days(days: str):
        days_list = days.split(",")
        result_days = []
        for ds in days_list:
            d = ds.split("-")
            if len(d) == 2:
                start_day, end_day = d
                start_day_index = DAYS_OF_WEEK.index(start_day)
                end_day_index = DAYS_OF_WEEK.index(end_day)
                result_days.extend(DAYS_OF_WEEK[start_day_index : end_day_index + 1])
            else:
                result_days.extend(d)
        return result_days

    opening_hours_blocks = split_and_clean(opening_hours_normalized)
    for opening_hours_block in opening_hours_blocks:
        opening_hours_block_parts = opening_hours_block.split(" ")
        if len(opening_hours_block_parts) == 1:
            # only hours, for all days
            days = DAYS_OF_WEEK
            hours = get_opening_hours(opening_hours_block_parts[0])
        elif len(opening_hours_block_parts) == 2:
            # days and hours
            days = get_opening_days(opening_hours_block_parts[0])
            hours = get_opening_hours(opening_hours_block_parts[1])
        else:
            raise ValueError(f"Invalid interval: {opening_hours_block}")

        for day in days:
            opening_hours_by_day_of_week[day].extend(hours)

    for day, hours in opening_hours_by_day_of_week.items():
        opening_hours_by_day_of_week[day] = merge_consecutive_tuples(hours)

    return opening_hours_by_day_of_week
