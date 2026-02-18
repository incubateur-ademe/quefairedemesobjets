from datetime import datetime, timezone

import pytest

from stats.utils import floor_to_period, parse_date, shift_period


@pytest.mark.parametrize(
    ("periodicity", "date", "expected"),
    [
        ("day", datetime(2024, 5, 17, 14, 45), datetime(2024, 5, 17)),
        ("week", datetime(2024, 5, 15, 23, 59), datetime(2024, 5, 13)),
        ("month", datetime(2024, 1, 31, 10, 0), datetime(2024, 1, 1)),
        ("year", datetime(2024, 8, 15, 8, 30), datetime(2024, 1, 1)),
    ],
)
def test_floor_to_period(periodicity, date, expected):
    assert floor_to_period(date, periodicity) == expected


def test_floor_to_period_invalid_periodicity():
    with pytest.raises(ValueError):
        floor_to_period(datetime(2024, 1, 1), "invalid")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("periodicity", "date", "steps", "expected"),
    [
        ("day", datetime(2024, 5, 10, 10, 0), 3, datetime(2024, 5, 13)),
        ("week", datetime(2024, 5, 10, 10, 0), -1, datetime(2024, 4, 29)),
        ("month", datetime(2024, 1, 31, 12, 0), 2, datetime(2024, 3, 1)),
        ("month", datetime(2024, 6, 15, 12, 0), -4, datetime(2024, 2, 1)),
        ("year", datetime(2024, 5, 10, 10, 0), 2, datetime(2026, 1, 1)),
    ],
)
def test_shift_period(periodicity, date, steps, expected):
    assert shift_period(date, periodicity, steps) == expected


def test_shift_period_invalid_periodicity():
    with pytest.raises(ValueError):
        shift_period(datetime(2024, 1, 1), "invalid", 1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("date_str", "expected"),
    [
        ("2024-01-01", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("1999-12-31", datetime(1999, 12, 31, tzinfo=timezone.utc)),
    ],
)
def test_parse_date_valid(date_str, expected):
    result = parse_date(date_str)
    assert result == expected
    assert result.tzinfo == timezone.utc


@pytest.mark.parametrize("date_str", ["", "2024/01/01", "01-01-2024"])
def test_parse_date_invalid(date_str):
    with pytest.raises(ValueError):
        parse_date(date_str)
