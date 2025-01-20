import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.tasks.business_logic.cluster_acteurs_info_size1 import (
    cluster_info_size1_exact_fields,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_info_size1_exact_fields"
    ============================================================

    💡 quoi: affichage des infos sur les clusters de taille 1 qui
    ne seront pas considérés pour le clustering sur la base du
    groupe avec les champs à match exact

    🎯 pourquoi: comprendre quels champs à match exact sont responsables
    pour la perte de ses clusters de taille 1

    🏗️ comment: on effectue le groupage en rajoutant les champs
    progressivement (champ1 -> champ1 + champ2 -> champ1 + champ2 + champ3)
    de manière à identifier l'impact de l'ajout des champs
    """


def cluster_info_size1_exact_fields_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    params = kwargs["ti"].xcom_pull(
        key="params", task_ids="cluster_acteurs_config_validate"
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_db_data_read_acteurs"
    )

    log.preview("paramètres reçus", params)
    log.preview("acteurs sélectionnés", df)

    results = cluster_info_size1_exact_fields(
        df=df,
        cluster_fields_exact=params["cluster_fields_exact"],
    )
    for group, result in results.items():
        msg = log.banner_string(f"📦 Groupage sur: {group}")
        msg += f"\n 🔴 Nombre de clusters de taille 1 ignorés: {result['count']}"
        logger.info(msg)
        log.preview_df_as_markdown("Echantillon:", result["sample"].head(100))


def cluster_acteurs_info_size1_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_info_size1",
        python_callable=cluster_info_size1_exact_fields_wrapper,
        dag=dag,
    )
