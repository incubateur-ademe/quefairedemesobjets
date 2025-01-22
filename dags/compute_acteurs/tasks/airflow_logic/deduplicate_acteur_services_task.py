import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import deduplicate_acteur_services
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def deduplicate_acteur_services_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="deduplicate_acteur_services",
        python_callable=deduplicate_acteur_services_wrapper,
        dag=dag,
    )


def deduplicate_acteur_services_wrapper(**kwargs):

    df_children = kwargs["ti"].xcom_pull(task_ids="compute_acteur")["df_children"]
    df_acteur_services = kwargs["ti"].xcom_pull(task_ids="compute_acteur_services")

    log.preview("df_children", df_children)
    log.preview("df_merged_relationship", df_acteur_services)

    return deduplicate_acteur_services(
        df_children=df_children,
        df_acteur_services=df_acteur_services,
    )
