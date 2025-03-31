"""Configuration models enrich DAG"""

import re
from typing import Optional

from pydantic import BaseModel

SEPARATOR_FILTER_FIELD = "__"


def filters_get(model: BaseModel, prefix: str) -> list[dict[str, str]]:
    """Utility to get list of filters (field, value) to apply to the data,
    used 2 ways:
        - generate the Airflow params for the UI from field names only
        - read Airflow params to generate filters with values

    Thus we have a dynamic Airflow UI controlled by and always aligned with
    our config model by only maintaining the latter.
    """
    filters = []
    for field in model.model_fields:
        if re.fullmatch(f"{prefix}{SEPARATOR_FILTER_FIELD}[a-z_]+", field):
            filters.append(
                {
                    "field": field.replace(f"{prefix}{SEPARATOR_FILTER_FIELD}", ""),
                    "value": getattr(model, field),
                }
            )
    return filters


class EnrichBaseConfig(BaseModel):
    dry_run: bool
    filter_contains__commentaires: Optional[str] = "test"
    filter_contains__nom: Optional[str]
    filter_equals__statut: Optional[str]

    def filters_contains(self) -> list[dict[str, str]]:
        return filters_get(self, "filter_contains")

    def filters_equals(self) -> list[dict[str, str]]:
        return filters_get(self, "filter_equals")


class EnrichClosedConfig(EnrichBaseConfig):
    filter_contains__naf: Optional[str]
