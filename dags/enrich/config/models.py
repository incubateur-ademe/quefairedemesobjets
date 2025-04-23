"""Configuration models enrich DAG"""

import re
from typing import Optional

from pydantic import BaseModel, Field, computed_field

SEPARATOR_FILTER_FIELD = "__"
FIELD_DBT_MODEL_REFRESH = Field(
    default=True,
    description="""🔄 Si coché, les modèles DBT seront rafraîchis.
        🔴 Désactiver uniquement pour des tests.""",
)
FIELD_DBT_MODEL_REFRESH_COMMAND = Field(
    default="",
    description="🔄 Commande DBT à exécuter pour rafraîchir les modèles",
)


def filters_get(model: BaseModel, prefix: str, operator: str) -> list[dict[str, str]]:
    """Utility to get list of filters (field, value) to apply to the data,
    used 2 ways:
        - generate the Airflow params for the UI from field names only
        - read Airflow params to generate filters with values

    Thus we have a dynamic Airflow UI controlled by and always aligned with
    our config model by only maintaining the latter.
    """
    filters = []
    for field in model.model_fields:
        value = getattr(model, field)
        if re.fullmatch(f"{prefix}{SEPARATOR_FILTER_FIELD}[a-z_]+", field):

            # Skipping None if it's not exclitely is_null operator
            if value is None and operator != "is_null":
                continue

            filters.append(
                {
                    "field": field.replace(f"{prefix}{SEPARATOR_FILTER_FIELD}", ""),
                    "operator": operator,
                    "value": value,
                }
            )
    return filters


class BaseConfig(BaseModel):
    dry_run: bool = Field(
        default=True,
        description="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
    )


class EnrichBaseConfig(BaseConfig):
    dbt_models_refresh: bool = FIELD_DBT_MODEL_REFRESH
    dbt_models_refresh_command: str = FIELD_DBT_MODEL_REFRESH_COMMAND
    filter_contains__acteur_commentaires: Optional[str] = Field(
        default=None,
        description="🔍 Filtre sur **acteur_commentaires**",
    )
    filter_contains__acteur_nom: Optional[str] = Field(
        default=None,
        description="🔍 Filtre sur **acteur_nom**",
    )
    filter_equals__acteur_statut: Optional[str] = Field(
        default=None,
        description="🔍 Filtre sur **acteur_statut**",
    )

    def filters_contains(self) -> list[dict[str, str]]:
        return filters_get(self, "filter_contains", "contains")

    def filters_equals(self) -> list[dict[str, str]]:
        return filters_get(self, "filter_equals", "equals")

    @computed_field
    @property
    def filters(self) -> list[dict[str, str]]:
        return self.filters_contains() + self.filters_equals()


class EnrichActeursClosedConfig(EnrichBaseConfig):
    filter_contains__etab_naf: Optional[str] = Field(
        default=None,
        description="🔍 Filtre sur **NAF AE Etablissement**",
    )


class EnrichActeursPropertiesConfig(BaseConfig):
    """This model doesn't build any suggestions so filter
    fields are not needed. We could inherit from EnrichBaseConfig
    and use pydantic exclude but which ends up being more work than
    just defining the 2 fields we need:
    https://docs.pydantic.dev/latest/concepts/fields/#exclude"""

    dbt_models_refresh: bool = FIELD_DBT_MODEL_REFRESH
    dbt_models_refresh_command: str = FIELD_DBT_MODEL_REFRESH_COMMAND


DAG_ID_TO_CONFIG_MODEL = {
    "enrich_acteurs_closed": EnrichActeursClosedConfig,
    "enrich_acteurs_properties": EnrichActeursPropertiesConfig,
}
