import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.business_logic.cluster_acteurs_df_sort import cluster_acteurs_df_sort
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

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids="cluster_acteurs_config_create"
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_normalize"
    )
    if df.empty:
        raise ValueError("Pas de données acteurs normalisées récupérées")

    log.preview("config reçue", config)
    log.preview("acteurs normalisés", df)

    df_suggestions = cluster_acteurs_suggestions(
        df,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
        cluster_fields_separate=config.cluster_fields_separate,
        cluster_fuzzy_threshold=config.cluster_fuzzy_threshold,
    )
    if df_suggestions.empty:
        raise AirflowSkipException(
            log.banner_string("Pas de suggestions de clusters générées")
        )

    df_suggestions = cluster_acteurs_df_sort(
        df_suggestions,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
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
