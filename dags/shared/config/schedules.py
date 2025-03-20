"""Constants for configuring DAG schedules"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SCHEDULES:
    DAILY: str = "0 0 * * *"
