import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import (
    TASK_CLUSTERS_DISPLAY,
    TASK_CONFIG_CREATE,
    TASK_NORMALIZE,
)
from cluster.tasks.business_logic.cluster_acteurs_clusters_display import (
    cluster_acteurs_clusters_display,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()


logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_CLUSTERS_DISPLAY}"
    ============================================================

    💡 quoi: génère des suggestions de clusters pour les acteurs

    🎯 pourquoi: c'est le but de ce DAG :)

    🏗️ comment: les suggestions sont générées après la normalisation
    avec les paramètres cluster_ du DAG
    """


def cluster_acteurs_suggestions_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_NORMALIZE)
    if df.empty:
        raise AirflowSkipException("Pas de données acteurs normalisées récupérées")

    log.preview("config reçue", config)
    # Zoom sur les champs de config de clustering pour + de clarté
    for key, value in config.__dict__.items():
        if key.startswith("cluster_"):
            log.preview(f"config.{key}", value)
    log.preview("acteurs normalisés", df)

    df = cluster_acteurs_clusters_display(
        df=df,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
        cluster_fields_separate=config.cluster_fields_separate,
        cluster_fuzzy_threshold=config.cluster_fuzzy_threshold,
        fields_protected=config.fields_protected,
        fields_transformed=config.fields_transformed,
    )

    # On pousse les suggestions dans xcom pour les tâches suivantes
    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_clusters_display_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_CLUSTERS_DISPLAY,
        python_callable=cluster_acteurs_suggestions_wrapper,
        provide_context=True,
        dag=dag,
    )
