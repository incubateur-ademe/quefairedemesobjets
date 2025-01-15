import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.tasks.business_logic.cluster_acteurs_suggestions import (
    cluster_acteurs_suggestions,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_suggestions"
    ============================================================

    💡 quoi: génère des suggestions de clusters pour les acteurs

    🎯 pourquoi: c'est le but de ce DAG :)

    🏗️ comment: les suggestions sont générées après la normalisation
    avec les paramètres cluster_ du DAG
    """


def cluster_acteurs_suggestions_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    params = kwargs["ti"].xcom_pull(
        key="params", task_ids="cluster_acteurs_config_validate"
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_normalize"
    )
    if df.empty:
        raise ValueError("Pas de données acteurs normalisées récupérées")

    log.preview("paramètres reçus", params)
    log.preview("acteurs normalisés", df)

    # Par défaut on ne clusterise pas les acteurs d'une même source
    cluster_fields_separate = ["source_id"]
    if params["cluster_intra_source_is_allowed"]:
        cluster_fields_separate = []

    df_suggestions = cluster_acteurs_suggestions(
        df,
        cluster_fields_exact=params["cluster_fields_exact"],
        cluster_fields_fuzzy=params["cluster_fields_fuzzy"] or [],
        cluster_fields_separate=cluster_fields_separate,
        cluster_fuzzy_threshold=params["cluster_fuzzy_threshold"],
    )
    if df_suggestions.empty:
        raise AirflowSkipException(
            log.banner_string("Pas de suggestions de clusters générées")
        )

    log.preview_df_as_markdown("suggestions de clusters", df_suggestions)

    # On pousse les suggestions dans xcom pour les tâches suivantes
    kwargs["ti"].xcom_push(key="df", value=df_suggestions)


def cluster_acteurs_suggestions_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="cluster_acteurs_suggestions",
        python_callable=cluster_acteurs_suggestions_wrapper,
        provide_context=True,
        dag=dag,
    )
