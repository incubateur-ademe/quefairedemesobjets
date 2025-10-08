"""Configuration models enrich DAG"""

import re
from typing import Optional

from pydantic import BaseModel, Field, computed_field, field_validator
from utils.airflow_params import airflow_params_dropdown_codes_to_ids

SEPARATOR_FILTER_FIELD = "__"
MAPPING_ACTEUR_TYPE = airflow_params_dropdown_codes_to_ids("ActeurType")
MAPPING_SOURCE = airflow_params_dropdown_codes_to_ids("Source")


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
            if operator == "in" and value is None or len(value) == 0:
                continue

            filters.append(
                {
                    "field": field.replace(f"{prefix}{SEPARATOR_FILTER_FIELD}", ""),
                    "operator": operator,
                    "value": value,
                }
            )
    return filters


class EnrichBaseConfig(BaseModel):
    dry_run: bool = Field(
        default=False,
        description="🚱 Si coché, aucune tâche d'écriture ne sera effectuée",
    )
    dbt_models_refresh: bool = Field(
        default=True,
        description="""🔄 Si coché, les modèles DBT seront rafraîchis.
        🔴 Désactiver uniquement pour des tests.""",
    )
    dbt_models_refresh_command: str = Field(
        default="",
        description="🔄 Commande DBT à exécuter pour rafraîchir les modèles",
    )
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
    filter_in__acteur_type_id: Optional[list[int]] = Field(
        default=[],
        description="🔍 Filtre sur **acteur_type**",
        examples=list(MAPPING_ACTEUR_TYPE.keys()),  # type: ignore
        json_schema_extra={
            "values_display": MAPPING_ACTEUR_TYPE,  # type: ignore
        },
    )

    filter_in__acteur_source_id: Optional[list[int]] = Field(
        default=[],
        description="🔍 Filtre sur **source**",
        examples=list(MAPPING_SOURCE.keys()),  # type: ignore
        json_schema_extra={
            "values_display": MAPPING_SOURCE,  # type: ignore
        },
    )

    @computed_field
    @property
    def filters(self) -> list[dict[str, str]]:
        return (
            filters_get(self, "filter_contains", "contains")
            + filters_get(self, "filter_equals", "equals")
            + filters_get(self, "filter_in", "in")
        )

    @field_validator("filter_in__acteur_type_id", mode="before")
    def validate_filter_in_acteur_type_id(cls, v) -> list[int]:
        # Due to Airflow Params dropdowns via dict values_display,
        # values coming back from Airflow will be strings to convert back to int
        return [int(x) for x in v] if v else []

    @field_validator("filter_in__acteur_source_id", mode="before")
    def validate_filter_in_acteur_source_id(cls, v) -> list[int]:
        # Same as above
        return [int(x) for x in v] if v else []


class EnrichActeursClosedConfig(EnrichBaseConfig):
    dbt_models_refresh_command: str = Field(
        default="dbt build --select tag:marts,tag:enrich,tag:closed",
        description="🔄 Commande DBT à exécuter pour rafraîchir les modèles",
    )
    filter_contains__etab_naf: Optional[str] = Field(
        default=None,
        description="🔍 Filtre sur **NAF AE Etablissement**",
    )


class EnrichActeursRGPDConfig(EnrichBaseConfig):
    dbt_models_refresh_command: str = Field(
        default="dbt build --select tag:marts,tag:enrich,tag:rgpd",
        description="🔄 Commande DBT à exécuter pour rafraîchir les modèles",
    )


class EnrichDbtModelsRefreshConfig(BaseModel):
    dbt_models_refresh_commands: list[str] = Field(
        default=[],
        description="🔄 Liste de commandes DBT à exécuter pour rafraîchir les modèles",
    )


class EnrichActeursVillesConfig(EnrichBaseConfig):
    pass


DAG_ID_TO_CONFIG_MODEL = {
    "enrich_acteurs_closed": EnrichActeursClosedConfig,
    "enrich_acteurs_rgpd": EnrichActeursRGPDConfig,
    "enrich_dbt_models_refresh": EnrichDbtModelsRefreshConfig,
    "enrich_acteurs_villes": EnrichActeursVillesConfig,
}
