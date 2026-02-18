"""Constants for configuring DAG schedules"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SCHEDULES:
    EVERY_5_MINUTES: str = "*/5 * * * *"  # every 5 minutes
    EVERY_HOUR_AT_MIN_3: str = "3 * * * *"  # 3 minutes après chaque heure
    EVERY_DAY_AT_00_00: str = "0 0 * * *"  # every day at 00:00
    EVERY_DAY_AT_01_00: str = "0 1 * * *"
    EVERY_MONDAY_AT_00_00: str = "0 0 * * 1"  # every monday at 00:00
    EVERY_MONDAY_AT_01_00: str = "0 1 * * 1"  # every monday at 01:00
    EVERY_MONDAY_AT_02_00: str = "0 2 * * 1"  # every monday at 02:00
    EVERY_SUNDAY_AT_00_00: str = "0 0 * * 0"  # every sunday at 00:00
    EVERY_SUNDAY_AT_01_00: str = "0 1 * * 0"  # every sunday at 01:00
    EVERY_SUNDAY_AT_02_00: str = "0 2 * * 0"  # every sunday at 02:00
    EVERY_SUNDAY_AT_03_00: str = "0 3 * * 0"  # every sunday at 03:00
    EVERY_FIRST_DAY_OF_MONTH_AT_00_00: str = (
        "0 0 1 * *"  # every first day of the month at 00:00
    )
