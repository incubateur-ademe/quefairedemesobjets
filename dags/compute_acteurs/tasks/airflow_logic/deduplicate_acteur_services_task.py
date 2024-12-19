import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import deduplicate_acteur_serivces
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def deduplicate_acteur_serivces_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="deduplicate_acteur_serivces",
        python_callable=deduplicate_acteur_serivces_wrapper,
        dag=dag,
    )


def deduplicate_acteur_serivces_wrapper(**kwargs):

    df_children = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")[
        "df_children"
    ]
    df_merge_acteur_services = kwargs["ti"].xcom_pull(task_ids="merge_acteur_services")

    log.preview("df_children", df_children)
    log.preview("df_merged_relationship", df_merge_acteur_services)

    return deduplicate_acteur_serivces(
        df_children=df_children,
        df_merge_acteur_services=df_merge_acteur_services,
    )
