"""Performs syntax checks URLs and tries
to fix them/propose alternatives following
some business logic (e.g. if http -> first try https)"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from crawl.config.tasks import TASKS
from crawl.config.xcoms import XCOMS, xcom_pull, xcom_push
from crawl.tasks.business_logic.crawl_urls_check_syntax import crawl_urls_check_syntax

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CHECK_SYNTAX}"
    ============================================================

    💡 quoi: on essaye de résoudre la syntaxe des URLs
    (ex: "pas bon" -> NULL, "a.com" -> "https://a.com")

    🎯 pourquoi: éliminer les URLs qu'on a aucune chance d'atteindre
    et prioriser les autres selon des règles métier (ex: HTTPs > HTTP)
    pour maximiser nos chances de succès

    🏗️ comment: fonction qui essaye de corriger/suggérer des syntaxes
    d'URLs automatiquement en se basant sur des règles métier
    """


def crawl_urls_check_syntax_wrapper(ti) -> None:
    logger.info(task_info_get())

    df_syntax_ok, df_syntax_fail = crawl_urls_check_syntax(
        df=xcom_pull(ti, XCOMS.DF_READ, skip_if_empty=True),
    )

    xcom_push(ti, XCOMS.DF_SYNTAX_OK, df_syntax_ok)
    xcom_push(ti, XCOMS.DF_SYNTAX_FAIL, df_syntax_fail)


def crawl_urls_check_syntax_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CHECK_SYNTAX,
        python_callable=crawl_urls_check_syntax_wrapper,
        dag=dag,
    )
