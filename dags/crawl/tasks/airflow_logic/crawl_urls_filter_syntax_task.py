import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic import url_suggest_urls_to_crawl
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "crawl_urls_filter_syntax"
    ============================================================

    💡 quoi: On filtre sur les URLs qui nous semble possible
    de parcourir, par exemple on var par chercher à parcourir
    " OAcaoiz, aozcin aozifn a"

    🎯 pourquoi: réduire le bruit

    🏗️ comment: en utilisant la fonction url_suggest_urls_to_crawl
    qui génère des suggestions d'URLs à parcourir sur la base
    de la syntaxe d'une URL donnée
    """


def crawl_urls_filter_syntax_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df = kwargs["ti"].xcom_pull(key="df", task_ids="crawl_urls_select_from_db")
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("df vide: on devrait pas être ici")
    df["urls_to_try"] = df["url"].apply(url_suggest_urls_to_crawl)

    # On regroupe les colonnes d'URL ensemble
    # pour faciliter le debug
    cols_urls = ["url", "urls_to_try"]
    cols_all = [x for x in df.columns if x not in cols_urls] + cols_urls
    df = df[cols_all]

    df_discarded = df[df["urls_to_try"].isnull()]
    df_try = df[df["urls_to_try"].notnull()]

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(
        "🔴 URLs qu'on va pas essayer de parcourir", df_discarded
    )
    log.preview_df_as_markdown("🟢 URLs qu'on va essayer de parcourir", df_try)

    if df_try.empty:
        raise AirflowSkipException("Pas d'URLs à parcourir")

    # use xcom to pass the result to the next task
    kwargs["ti"].xcom_push(key="df_try", value=df_try)


def crawl_urls_filter_syntax_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="crawl_urls_filter_syntax",
        python_callable=crawl_urls_filter_syntax_wrapper,
        dag=dag,
    )
