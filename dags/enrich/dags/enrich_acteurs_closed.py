"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from airflow import DAG
from enrich.config import DBT, TASKS, XCOMS, EnrichActeursClosedConfig
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_read_dbt_model_task import (
    enrich_read_dbt_model_task,
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
            filter_equals__acteur_statut="ACTIF",
        )
    ),
) as dag:
    """
    chain(
        enrich_config_create_task(dag),
        enrich_read_dbt_model_task(
            dag,
            task_id=TASKS.READ_AE_CLOSED_CANDIDATES,
            dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_CANDIDATES,
            xcom_push_key=XCOMS.DF_CLOSED_CANDIDATES,
        ),
        enrich_read_dbt_model_task(
            dag,
            task_id=TASKS.READ_AE_CLOSED_REPLACED,
            dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_REPLACED,
            xcom_push_key=XCOMS.DF_CLOSED_REPLACED,
        ),
    )
    """
    config = enrich_config_create_task(dag)
    closed_candidates = enrich_read_dbt_model_task(
        dag,
        task_id=TASKS.READ_AE_CLOSED_CANDIDATES,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_CANDIDATES,
        xcom_push_key=XCOMS.DF_CLOSED_CANDIDATES,
    )
    closed_replaced = enrich_read_dbt_model_task(
        dag,
        task_id=TASKS.READ_AE_CLOSED_REPLACED,
        dbt_model_name=DBT.MARTS_ENRICH_AE_CLOSED_REPLACED,
        xcom_push_key=XCOMS.DF_CLOSED_REPLACED,
    )
    config >> closed_candidates
    config >> closed_replaced
