import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from crawl.tasks.business_logic import CrawlUrlModel, crawl_url
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "crawl_urls_try_to_solve"
    ============================================================

    💡 quoi: on essaye de parcourir les URLs

    🎯 pourquoi: proposer des suggestions à l'étape d'après sur
    les URLs qu'on a réussit à parcourir

    🏗️ comment: avec un crawler python tout simple
    """


def crawl_urls_try_to_solve_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df_try = kwargs["ti"].xcom_pull(key="df_try", task_ids="crawl_urls_filter_syntax")
    if not isinstance(df_try, pd.DataFrame) or df_try.empty:
        raise ValueError("df_try vide: on devrait pas être ici")
    log.preview_df_as_markdown("🟢 URLs qu'on va essayer de parcourir", df_try)

    df_try = df_try.rename(columns={"url": "url_original"})
    df_try["was_success"] = False
    df_try["urls_tried"] = 0
    df_try["url_success"] = None
    df_try["urls_results"] = df_try["urls_to_try"].apply(lambda x: [])
    for _, row in df_try.iterrows():
        if not row["urls_to_try"]:
            continue
        for url in row["urls_to_try"]:
            logger.info(f"🔍 CRAWL: {url}")
            result: CrawlUrlModel = crawl_url(url)
            df_try.at[_, "urls_tried"] += 1
            df_try.at[_, "urls_results"].append(result.model_dump())
            if result.was_success:
                df_try.at[_, "was_success"] = True
                df_try.at[_, "url_success"] = result.url_resolved
                break

    # On regroupe la colonne source/finale
    # pour faciliter le debug
    cols_urls = ["url_success", "url_original", "urls_to_try"]
    cols_all = cols_urls + [x for x in df_try.columns if x not in cols_urls]
    df_try = df_try[cols_all]

    df_failed = df_try[~df_try["was_success"]]
    df_success = df_try[df_try["was_success"]]
    df_diff = df_success[df_success["url_original"] != df_success["url_success"]]

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("🔴 URLs parcourues en échec", df_failed)
    log.preview_df_as_markdown("🟢 URLs parcourues en succès", df_success)
    log.preview_df_as_markdown("🟡 URLs parcourues en succès AVEC DIFF", df_diff)

    if df_diff.empty:
        raise AirflowSkipException(
            "Pas d'URLs résolues différentes = pas de suggestions"
        )

    # use xcom to pass the result to the next task
    kwargs["ti"].xcom_push(key="df_diff", value=df_diff)


def crawl_urls_try_to_solve_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="crawl_urls_try_to_solve",
        python_callable=crawl_urls_try_to_solve_wrapper,
        dag=dag,
    )
