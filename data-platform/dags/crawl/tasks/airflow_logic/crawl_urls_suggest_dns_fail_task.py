import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from crawl.config.cohorts import COHORTS
from crawl.config.tasks import TASKS
from crawl.config.xcoms import XCOMS, xcom_pull
from crawl.tasks.business_logic.crawl_urls_suggest import crawl_urls_suggest

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""

    ============================================================
    Description de la tâche "{TASKS.SUGGEST_DNS_FAIL}"
    ============================================================

    💡 quoi: suggestions pour {COHORTS.DNS_FAIL}

    🎯 pourquoi: mise à vide des domaines injoignables

    🏗️ comment: on génère les suggestions et on les
    écrit dans la base de données uniquement si dry_run=False
    """


def crawl_urls_suggest_dns_fail_wrapper(ti, params, dag, run_id) -> None:
    logger.info(task_info_get())

    crawl_urls_suggest(
        df=xcom_pull(ti, XCOMS.DF_DNS_FAIL, skip_if_empty=True),
        dag_display_name=dag.dag_display_name,
        run_id=run_id,
        dry_run=params.get("dry_run", True),
        use_legacy_suggestions=params.get("use_legacy_suggestions", True),
    )


def crawl_urls_suggest_dns_fail_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGEST_DNS_FAIL,
        python_callable=crawl_urls_suggest_dns_fail_wrapper,
        dag=dag,
    )
