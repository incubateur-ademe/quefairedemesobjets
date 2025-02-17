import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import (
    TASK_CONFIG_CREATE,
    TASK_NORMALIZE,
    TASK_SELECTION,
)
from cluster.tasks.business_logic.cluster_acteurs_normalize import (
    cluster_acteurs_normalize,
)
from cluster.tasks.business_logic.misc.df_sort import df_sort
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_NORMALIZE}"
    ============================================================

    💡 quoi: normalise les valeurs des champs normalize_fields

    🎯 pourquoi: pour accroite les chances de correspondance (soit
    exacte soit fuzzy)

    🏗️ comment: les normalisations sont appliquées dans l'ordre
    de la UI. Si un champ est spécifié dans plusieurs options,
    toutes les normalisations sont appliquées à la suite.
    """


def cluster_acteurs_normalize_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_SELECTION)
    if df.empty:
        raise ValueError("Pas de données acteurs récupérées")

    log.preview("config reçue", config)
    # Zoom sur les champs de config de normalisation pour + de clarté
    for key, value in config.__dict__.items():
        if key.startswith("normalize_"):
            log.preview(f"config.{key}", value)
    log.preview("acteurs sélectionnés", df)

    df_norm = cluster_acteurs_normalize(
        df,
        normalize_fields_basic=config.normalize_fields_basic,
        normalize_fields_no_words_size1=config.normalize_fields_no_words_size1,
        normalize_fields_no_words_size2_or_less=config.normalize_fields_no_words_size2_or_less,
        normalize_fields_no_words_size3_or_less=config.normalize_fields_no_words_size3_or_less,
        normalize_fields_order_unique_words=config.normalize_fields_order_unique_words,
    )

    # TODO: shows # uniques before and after per field

    log.preview("acteurs normalisés", df_norm)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    df_norm = df_sort(df_norm)
    log.preview_df_as_markdown("acteurs normalisés", df_norm)

    kwargs["ti"].xcom_push(key="df", value=df_norm)


def cluster_acteurs_normalize_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_NORMALIZE,
        python_callable=cluster_acteurs_normalize_wrapper,
        dag=dag,
    )
