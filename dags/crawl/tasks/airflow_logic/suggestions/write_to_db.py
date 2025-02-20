import logging

import crawl.tasks.airflow_logic.task_ids as TASK_IDS
from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic.suggestions.write_to_db import (
    crawl_urls_suggestions_write_to_db,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_IDS.SUGGESTIONS_PREPARE}"
    ============================================================

    💡 quoi: on génère les suggestions (mais on les écrit pas en DB)

    🎯 pourquoi: validation & affichage airflow avant écriture DB

    🏗️ comment: on récupère les URL traités par la tâche d'avant:
     - si succès ET différent: on suggère la nouvelle URL
     - si échec: on suggère du EMPTY
    """


def crawl_urls_suggestions_write_to_db_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    metadata = kwargs["ti"].xcom_pull(
        key="metadata", task_ids=TASK_IDS.SUGGESTIONS_METADATA
    )
    suggestions = kwargs["ti"].xcom_pull(
        key="suggestions", task_ids=TASK_IDS.SUGGESTIONS_PREPARE
    )
    crawl_urls_suggestions_write_to_db(
        metadata=metadata,
        suggestions=suggestions,
        identifiant_action=f"dag_id={kwargs['dag'].dag_id}",
        identifiant_execution=f"run_id={kwargs['run_id']}",
    )


def crawl_urls_suggestions_write_to_db_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_IDS.SUGGESTIONS_TO_DB,
        python_callable=crawl_urls_suggestions_write_to_db_wrapper,
        dag=dag,
    )
