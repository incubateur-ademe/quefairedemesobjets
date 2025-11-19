from __future__ import annotations

from typing import Literal, Optional

from ninja import Field, Schema

StatPeriodicity = Literal["day", "week", "month", "year"]


class StatInput(Schema):
    since: Optional[int] = Field(
        None,
        ge=1,
        description="Nombre d'itérations de la période souhaitée (ex: 30 jours).",
    )
    periodicity: StatPeriodicity = Field(
        "month",
        description="Granularité de regroupement des KPI.",
    )


class Stat(Schema):
    value: float
    date: int
    iso_date: str


class StatOutput(Schema):
    description: Optional[str] = None
    stats: list[Stat]
