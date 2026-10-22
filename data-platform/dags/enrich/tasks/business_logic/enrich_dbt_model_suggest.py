import logging

from enrich.tasks.business_logic.enrich_dbt_model_read import enrich_dbt_model_read
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestion_groupes import (
    enrich_dbt_model_to_suggestion_groupes,
)
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)

logger = logging.getLogger(__name__)


def enrich_dbt_model_suggest(
    dbt_model_name: str,
    filters: list[dict],
    cohort: str,
    identifiant_action: str,
    dry_run: bool = True,
    use_legacy_suggestions: bool = False,
) -> bool:
    """Reads a DBT model and generates suggestions for it"""
    df = enrich_dbt_model_read(dbt_model_name, filters)

    if df.empty:
        logger.info(f"0 donnée pour {dbt_model_name=} avec filtres {filters}")
        return False

    if use_legacy_suggestions:
        logger.warning("use_legacy_suggestions=True")
        return enrich_dbt_model_to_suggestions(df, cohort, identifiant_action, dry_run)

    logger.warning("use_legacy_suggestions=False")
    return enrich_dbt_model_to_suggestion_groupes(
        df, cohort, identifiant_action, dry_run
    )
