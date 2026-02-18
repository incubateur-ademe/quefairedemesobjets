"""Constants for configuring DAG start dates.
We have had issues on new DAGs with Airflow spamming
the scheduler despite catchup=False, so as extra safety
we configure start dates to be 1 interval in the past of schedule
(past needed so Airflow isn't stuck waiting for a constantly
present/future date) thus if there is catchup, it's only 1 run max."""

from dataclasses import dataclass
from datetime import datetime

import pendulum


@dataclass(frozen=True)
class START_DATES:
    DEFAULT: datetime = pendulum.datetime(2025, 8, 1, tz="UTC")
