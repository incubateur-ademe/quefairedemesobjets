"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from airflow import DAG
from enrich.config import (
    COHORTS,
    DBT,
    TASKS,
    EnrichActeursClosedConfig,
)
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_model_suggest_task import (
    enrich_dbt_model_suggest_task,
)
from enrich.tasks.airflow_logic.enrich_dbt_models_refresh_task import (
    enrich_dbt_models_refresh_task,
)
from shared.config import CATCHUPS, SCHEDULES, START_DATES, config_to_airflow_params

with DAG(
    dag_id="enrich_acteurs_closed",
    dag_display_name="🚪 Enrichir - Acteurs Fermés",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=(
        "Un DAG pour détécter et remplacer les acteurs fermés"
        "dans l'Annuaire Entreprises (AE)"
    ),
    tags=["annuaire", "entreprises", "ae", "siren", "siret", "acteurs", "fermés"],
    schedule=SCHEDULES.NONE,
    catchup=CATCHUPS.AWLAYS_FALSE,
    start_date=START_DATES.FOR_SCHEDULE_NONE,
    params=config_to_airflow_params(
        EnrichActeursClosedConfig(
            dbt_models_refresh=False,
            filter_equals__acteur_statut="ACTIF",
        )
    ),
) as dag:
    # Instantiation
    config = enrich_config_create_task(dag)
    dbt_refresh = enrich_dbt_models_refresh_task(dag)
    suggest_not_replaced = enrich_dbt_model_suggest_task(
        dag,
        task_id=TASKS.ENRICH_CLOSED_SUGGESTIONS_NOT_REPLACED,
        cohort=COHORTS.CLOSED_NOT_REPLACED,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_NOT_REPLACED,
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
    dbt_refresh >> suggest_not_replaced  # type: ignore
    dbt_refresh >> suggest_other_siren  # type: ignore
    dbt_refresh >> suggest_same_siren  # type: ignore
