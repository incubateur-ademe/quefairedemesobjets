import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import merge_acteur_services
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def merge_acteur_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="merge_acteur_services",
        python_callable=merge_acteur_services_wrapper,
        dag=dag,
    )


def merge_acteur_services_wrapper(**kwargs):
    df_acteur_acteur_services = kwargs["ti"].xcom_pull(
        task_ids="load_acteur_acteur_services"
    )
    df_revisionacteur_acteur_services = kwargs["ti"].xcom_pull(
        task_ids="load_revisionacteur_acteur_services"
    )
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    log.preview("df_acteur_acteur_services", df_acteur_acteur_services)
    log.preview("df_revisionacteur_acteur_services", df_revisionacteur_acteur_services)
    log.preview("df_revisionacteur", df_revisionacteur)

    return merge_acteur_services(
        df_acteur_acteur_services=df_acteur_acteur_services,
        df_revisionacteur_acteur_services=df_revisionacteur_acteur_services,
        df_revisionacteur=df_revisionacteur,
    )
