import logging

import crawl.config.tasks as TASKS
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.config.xcom import XCOM_SUGGESTIONS_META, XCOM_SUGGESTIONS_PREP, xcom_pull
from crawl.tasks.business_logic.crawl_urls_suggestions_to_db import (
    crawl_urls_suggestions_write_to_db,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SUGGESTIONS_PREP}"
    ============================================================

    💡 quoi: on génère les suggestions (mais on les écrit pas en DB)

    🎯 pourquoi: validation & affichage airflow avant écriture DB

    🏗️ comment: on récupère les URL traités par la tâche d'avant:
     - si succès ET différent: on suggère la nouvelle URL
     - si échec: on suggère du EMPTY
    """


def crawl_urls_suggestions_write_to_db_wrapper(params, ti, dag, run_id) -> None:
    logger.info(task_info_get())

    if params["dry_run"] is not False:
        raise AirflowSkipException("Dry run, on s'arrête là")

    crawl_urls_suggestions_write_to_db(
        metadata=xcom_pull(ti, XCOM_SUGGESTIONS_META),
        suggestions=xcom_pull(ti, XCOM_SUGGESTIONS_PREP),
        identifiant_action=f"dag_id={dag.dag_id}",
        identifiant_execution=f"run_id={run_id}",
    )


def crawl_urls_suggestions_write_to_db_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGESTIONS_TO_DB,
        python_callable=crawl_urls_suggestions_write_to_db_wrapper,
        dag=dag,
    )
