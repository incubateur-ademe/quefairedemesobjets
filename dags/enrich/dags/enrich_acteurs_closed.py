"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from airflow import DAG
from enrich.config.cohorts import COHORTS
from enrich.config.dbt import DBT
from enrich.config.models import EnrichActeursClosedConfig
from enrich.config.tasks import TASKS
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_model_suggest_task import (
    enrich_dbt_model_suggest_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_models_refresh_task import (
    enrich_dbt_models_refresh_task,
)
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.models import config_to_airflow_params
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="enrich_acteurs_closed",
    dag_display_name="🚪 Enrichir - Acteurs Fermés",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    description=(
        "Un DAG pour détécter et remplacer les acteurs fermés"
        "dans l'Annuaire Entreprises (AE)"
    ),
    tags=[
        TAGS.ENRICH,
        TAGS.ANNAIRE_ENTREPRISE,
        TAGS.SIREN,
        TAGS.SIRET,
        TAGS.ACTEURS,
        TAGS.CLOSED,
    ],
    schedule=None,
    start_date=START_DATES.DEFAULT,
    params=config_to_airflow_params(
        EnrichActeursClosedConfig(
            dbt_models_refresh=True,
            dbt_models_refresh_command=(
                "dbt build --select tag:marts,tag:enrich,tag:closed"
            ),
            filter_equals__acteur_statut="ACTIF",
        )
    ),
) as dag:
    # Instantiation
    config = enrich_config_create_task(dag)
    dbt_refresh = enrich_dbt_models_refresh_task(dag)
    suggest_not_replaced_unite = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_NOT_REPLACED_UNITE,
        cohort=COHORTS.CLOSED_NOT_REPLACED_UNITE,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_NOT_REPLACED_UNITE,
    )
    suggest_not_replaced_etablissement = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_NOT_REPLACED_ETABLISSEMENT,
        cohort=COHORTS.CLOSED_NOT_REPLACED_ETABLISSEMENT,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_NOT_REPLACED_ETABLISSEMENT,
    )
    suggest_other_siren = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_OTHER_SIREN,
        cohort=COHORTS.CLOSED_REP_OTHER_SIREN,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_REPLACED_OTHER_SIREN,
    )
    suggest_same_siren = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_SAME_SIREN,
        cohort=COHORTS.CLOSED_REP_SAME_SIREN,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_REPLACED_SAME_SIREN,
    )

    # Graph
    config >> dbt_refresh  # type: ignore
    dbt_refresh >> suggest_not_replaced_unite  # type: ignore
    dbt_refresh >> suggest_not_replaced_etablissement  # type: ignore
    dbt_refresh >> suggest_other_siren  # type: ignore
    dbt_refresh >> suggest_same_siren  # type: ignore
