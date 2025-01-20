import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.tasks.business_logic.cluster_acteurs_df_sort import cluster_acteurs_df_sort
from cluster.tasks.business_logic.cluster_acteurs_normalize import (
    cluster_acteurs_normalize,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_normalize_task"
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
    params = kwargs["ti"].xcom_pull(
        key="params", task_ids="cluster_acteurs_config_validate"
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_db_data_read_acteurs"
    )
    if df.empty:
        raise ValueError("Pas de données acteurs récupérées")

    log.preview("paramètres reçus", params)
    log.preview("acteurs sélectionnés", df)

    df_norm = cluster_acteurs_normalize(
        df,
        # Par défaut si on ne précise pas de champs,
        # on applique la normalisation basique à tous les champs
        normalize_fields_basic=params["normalize_fields_basic"] or [],
        normalize_fields_no_words_size1=params["normalize_fields_no_words_size1"] or [],
        normalize_fields_no_words_size2_or_less=params[
            "normalize_fields_no_words_size2_or_less"
        ]
        or [],
        normalize_fields_no_words_size3_or_less=params[
            "normalize_fields_no_words_size3_or_less"
        ]
        or [],
        # Pareil, par défaut on applique à tous les champs
        normalize_fields_order_unique_words=params[
            "normalize_fields_order_unique_words"
        ]
        or [],
    )

    # TODO: shows # uniques before and after per field

    log.preview("acteurs normalisés", df_norm)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    df_norm = cluster_acteurs_df_sort(df_norm)
    log.preview_df_as_markdown("acteurs normalisés", df_norm)

    # Les XCOM étant spécifiques à une tâche on peut pousser
    # le même nom sans risque de collision. Ainsi, pousse le nom "df"
    # et pas "df_norm" pour avoir toujours le nom "df" à travers
    # toutes les tâches et pas avoir à se rappeler de la nomenclature
    # des tâches précédentes.
    kwargs["ti"].xcom_push(key="df", value=df_norm)


def cluster_acteurs_normalize_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_normalize",
        python_callable=cluster_acteurs_normalize_wrapper,
        dag=dag,
    )
