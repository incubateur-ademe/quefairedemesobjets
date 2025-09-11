import pandas as pd
from enrich.config.cohorts import COHORTS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)


def db_write_cp_suggestions(
    df_acteur_cp: pd.DataFrame,
    df_revision_acteur_cp: pd.DataFrame,
    identifiant_action: str,
    dry_run: bool = True,
) -> None:
    """Write cp suggestions to db"""

    enrich_dbt_model_to_suggestions(
        df=df_acteur_cp,
        cohort=COHORTS.ACTEUR_CP_TYPO,
        identifiant_action=identifiant_action,
        dry_run=dry_run,
    )
    enrich_dbt_model_to_suggestions(
        df=df_revision_acteur_cp,
        cohort=COHORTS.REVISION_ACTEUR_CP_TYPO,
        identifiant_action=identifiant_action,
        dry_run=dry_run,
    )
