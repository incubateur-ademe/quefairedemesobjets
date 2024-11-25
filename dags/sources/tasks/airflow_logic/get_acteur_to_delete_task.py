import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from sources.tasks.business_logic.propose_acteur_to_delete import (
    propose_acteur_to_delete,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_acteur_to_delete_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="propose_acteur_to_delete",
        python_callable=propose_acteur_to_delete_wrapper,
        dag=dag,
    )


def propose_acteur_to_delete_wrapper(**kwargs):
    df_acteurs_for_source = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")[
        "df"
    ]
    df_acteurs_from_db = kwargs["ti"].xcom_pull(task_ids="db_read_acteur")

    log.preview(df_acteurs_for_source, "df_acteurs_for_source")
    log.preview(df_acteurs_from_db, "df_acteurs_from_db")

    return propose_acteur_to_delete(
        df_acteurs_for_source=df_acteurs_for_source,
        df_acteurs_from_db=df_acteurs_from_db,
    )
