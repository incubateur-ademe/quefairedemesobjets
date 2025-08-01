"""Constants for configuring DAG schedules"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SCHEDULES:
    HOURLY: str = "3 * * * *"  # 3 minutes après chaque heure
    DAILY: str = "0 0 * * *"
    DAILY_AT_1AM: str = "0 1 * * *"
    WEEKLY: str = "0 0 * * 1"
    WEEKLY_AT_1AM: str = "0 1 * * 1"
    MONTHLY: str = "0 0 1 * *"
    NONE = None
