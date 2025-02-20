import logging

import crawl.tasks.airflow_logic.task_ids as TASK_IDS
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic.solve.syntax import crawl_urls_solve_syntax
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_IDS.SOLVE_SYNTAX}"
    ============================================================

    💡 quoi: on essaye de résoudre la syntaxe des URLs
    (ex: "pas bon" -> NULL, "a.com" -> "https://a.com")

    🎯 pourquoi: éliminer les URLs qu'on a aucune chance d'atteindre
    et prioriser les autres selon des règles métier (ex: HTTPs > HTTP)
    pour maximiser nos chances de succès

    🏗️ comment: fonction qui essaye de corriger/suggérer des syntaxes
    d'URLs automatiquement en se basant sur des règles métier
    """


def crawl_urls_solve_syntax_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_IDS.GROUPBY_URL)
    df_try, df_discarded = crawl_urls_solve_syntax(df)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("🔴 URLs pas à parcourir", df_discarded)
    log.preview_df_as_markdown("🟢 URLs à parcourir", df_try)

    if df_try.empty:
        raise AirflowSkipException("Pas d'URLs à parcourir = on s'arrête là")

    kwargs["ti"].xcom_push(key="df", value=df_try)


def crawl_urls_solve_syntax_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_IDS.SOLVE_SYNTAX,
        python_callable=crawl_urls_solve_syntax_wrapper,
        dag=dag,
    )
