import logging

import crawl.tasks.airflow_logic.task_ids as TASK_IDS
from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic.suggestions.prepare import (
    crawl_urls_suggestions_prepare,
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


def crawl_urls_suggestions_prepare_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df_ok_diff = kwargs["ti"].xcom_pull(key="df_ok_diff", task_ids=TASK_IDS.SOLVE_REACH)
    df_fail = kwargs["ti"].xcom_pull(key="df_fail", task_ids=TASK_IDS.SOLVE_REACH)
    suggestions = crawl_urls_suggestions_prepare(df_ok_diff=df_ok_diff, df_fail=df_fail)
    if not suggestions:
        raise ValueError("Si est on arrivé ici, on devrait avoir des suggestions")

    kwargs["ti"].xcom_push(key="suggestions", value=suggestions)


def crawl_urls_suggestions_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_IDS.SUGGESTIONS_PREPARE,
        python_callable=crawl_urls_suggestions_prepare_wrapper,
        dag=dag,
    )
