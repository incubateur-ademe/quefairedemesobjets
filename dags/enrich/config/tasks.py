"""Task IDs for RGPD anonymize people DAG"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TASKS:
    # Config
    CONFIG_CREATE: str = "enrich_config_create"

    # Read tasks
    ENRICH_CLOSED_REPLACED_SAME_SIREN: str = "enrich_acteurs_closed_replaced_same_siren"
    ENRICH_CLOSED_REPLACED_OTHER_SIREN: str = (
        "enrich_acteurs_closed_replaced_other_siren"
    )
    ENRICH_CLOSED_NOT_REPLACED: str = "enrich_acteurs_closed_not_replaced"
    ENRICH_CLOSED_SUGGESTIONS_SAME_SIREN: str = (
        "enrich_acteurs_closed_suggestions_same_siren"
    )
    ENRICH_CLOSED_SUGGESTIONS_OTHER_SIREN: str = (
        "enrich_acteurs_closed_suggestions_other_siren"
    )
    ENRICH_CLOSED_SUGGESTIONS_NOT_REPLACED: str = (
        "enrich_acteurs_closed_suggestions_not_replaced"
    )
    ENRICH_DBT_MODELS_REFRESH: str = "enrich_dbt_models_refresh"
