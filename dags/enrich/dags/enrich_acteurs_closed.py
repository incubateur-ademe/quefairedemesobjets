"""
DAG to anonymize QFDMO acteur which names
contains people from Annuaire Entreprise (AE)
"""

from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from enrich.config import DBT, TASKS, XCOMS, EnrichActeursClosedConfig
from enrich.tasks.airflow_logic.enrich_config_create_task import (
    enrich_config_create_task,
)
from enrich.tasks.airflow_logic.enrich_read_dbt_model_task import (
    enrich_read_dbt_model_task,
)
from shared.config.models import config_to_airflow_params

with DAG(
    dag_id="enrich_acteurs_closed",
    dag_display_name="🚪 Enrichir - Acteurs Fermés",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2025, 3, 5),
        "catchup": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    description=(
        "Un DAG pour détécter et remplacer les acteurs fermés"
        "dans l'Annuaire Entreprises (AE)"
    ),
    tags=["annuaire", "entreprises", "ae", "siren", "siret", "acteurs", "fermés"],
    schedule=None,
    catchup=False,
    params=config_to_airflow_params(
        EnrichActeursClosedConfig(
            filter_equals__acteur_statut="ACTIF",
        )
    ),
) as dag:
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
