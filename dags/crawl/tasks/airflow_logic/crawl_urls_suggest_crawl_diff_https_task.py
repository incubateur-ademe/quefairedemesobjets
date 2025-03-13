import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl.config.cohorts import COHORTS
from crawl.config.tasks import TASKS
from crawl.config.xcoms import XCOMS, xcom_pull
from crawl.tasks.business_logic.crawl_urls_suggest import crawl_urls_suggest
from utils.dataframes import df_none_or_empty

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""

    ============================================================
    Description de la tâche "{TASKS.SUGGEST_CRAWL_DIFF_HTTPS}"
    ============================================================

    💡 quoi: suggestions pour {COHORTS.CRAWL_DIFF_HTTPS}

    🎯 pourquoi: URLs joignables avec redirection HTTPs

    🏗️ comment: on génère les suggestions et on les
    écrit dans la base de données uniquement si dry_run=False
    """


def crawl_urls_suggest_crawl_diff_https_wrapper(ti, params, dag, run_id) -> None:
    logger.info(task_info_get())

    df = xcom_pull(ti, XCOMS.DF_CRAWL_DIFF_HTTPS)
    # TODO: refactor below with task dependencies once DAG is no longer linear
    if df_none_or_empty(df):
        logger.info("Pas d'URLs différentes HTTPs, on s'arrête là")
        return
    crawl_urls_suggest(
        df=df, dag_id=dag.dag_id, run_id=run_id, dry_run=params.get("dry_run", True)
    )


def crawl_urls_suggest_crawl_diff_https_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGEST_CRAWL_DIFF_HTTPS,
        python_callable=crawl_urls_suggest_crawl_diff_https_wrapper,
        dag=dag,
    )
