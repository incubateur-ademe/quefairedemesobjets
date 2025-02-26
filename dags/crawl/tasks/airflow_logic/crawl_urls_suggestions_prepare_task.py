"""Prepares suggestions as a list of dicts. Suggestions are
validated ONLY with their SuggestionChange pydantic model
and NOT the Suggestion Django model which depends on creating
a SuggestionCohorte in DB which we want to keep for last when
we know all suggestions are ready to be written in DB"""

import logging

import crawl.config.tasks as TASKS
from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.config.xcom import (
    XCOM_DF_DNS_FAIL,
    XCOM_DF_SYNTAX_FAIL,
    XCOM_DF_URLS_FAIL,
    XCOM_DF_URLS_OK_DIFF,
    XCOM_SUGGESTIONS_PREP,
    xcom_pull,
)
from crawl.tasks.business_logic.crawl_urls_suggestions_prepare import (
    crawl_urls_suggestions_prepare,
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


def crawl_urls_suggestions_prepare_wrapper(ti) -> None:
    logger.info(task_info_get())

    suggestions = crawl_urls_suggestions_prepare(
        df_syntax_fail=xcom_pull(ti, XCOM_DF_SYNTAX_FAIL),
        df_dns_fail=xcom_pull(ti, XCOM_DF_DNS_FAIL),
        df_urls_ok_diff=xcom_pull(ti, XCOM_DF_URLS_OK_DIFF),
        df_urls_fail=xcom_pull(ti, XCOM_DF_URLS_FAIL),
    )

    ti.xcom_push(key=XCOM_SUGGESTIONS_PREP, value=suggestions)


def crawl_urls_suggestions_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGESTIONS_PREP,
        python_callable=crawl_urls_suggestions_prepare_wrapper,
        dag=dag,
    )
