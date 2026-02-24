import logging

import pandas as pd
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.providers.standard.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.config.tasks import TASKS
from cluster.config.xcoms import XCOMS, xcom_pull
from cluster.tasks.business_logic.cluster_acteurs_clusters_prepare import (
    cluster_acteurs_clusters_prepare,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()


logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CLUSTERS_PREPARE}"
    ============================================================

    💡 quoi: génère des suggestions de clusters pour les acteurs

    🎯 pourquoi: c'est le but de ce DAG :)

    🏗️ comment: les suggestions sont générées après la normalisation
    avec les paramètres cluster_ du DAG
    """


def cluster_acteurs_clusters_prepare_wrapper(ti) -> None:
    logger.info(task_info_get())

    config: ClusterConfig = xcom_pull(ti, XCOMS.CONFIG)
    df: pd.DataFrame = xcom_pull(ti, XCOMS.DF_NORMALIZE)

    if df.empty:
        raise AirflowSkipException("Pas d'acteurs normalisés, on devrait pas être là")

    log.preview("config reçue", config)
    log.preview_dict_subsets(config.__dict__, key_pattern="cluster_")
    log.preview("acteurs normalisés", df)

    df = cluster_acteurs_clusters_prepare(
        df=df,
        cluster_fields_exact=config.cluster_fields_exact,
        cluster_fields_fuzzy=config.cluster_fields_fuzzy,
        cluster_fuzzy_threshold=config.cluster_fuzzy_threshold,
        cluster_intra_source_is_allowed=config.cluster_intra_source_is_allowed,
        fields_protected=config.fields_protected,
        fields_transformed=config.fields_transformed,
        include_source_ids=config.include_source_ids,
    )

    if df.empty:
        raise AirflowSkipException("Pas de clusters trouvés, on s'arrête là")

    ti.xcom_push(key=XCOMS.DF_CLUSTERS_PREPARE, value=df)


def cluster_acteurs_clusters_prepare_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CLUSTERS_PREPARE,
        python_callable=cluster_acteurs_clusters_prepare_wrapper,
        dag=dag,
    )
