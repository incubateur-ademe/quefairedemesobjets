import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from compute_acteurs.tasks.business_logic import deduplicate_acteur_sources
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def deduplicate_acteur_sources_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="deduplicate_acteur_sources",
        python_callable=deduplicate_acteur_sources_wrapper,
        dag=dag,
    )


def deduplicate_acteur_sources_wrapper(**kwargs):

    data_actors = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")
    df_children = data_actors["df_children"]
    df_acteur_merged = data_actors["df_acteur_merged"]

    log.preview("df_children", df_children)
    log.preview("df_acteur_merged", df_acteur_merged)

    return deduplicate_acteur_sources(
        df_children=df_children,
        df_acteur_merged=df_acteur_merged,
    )
