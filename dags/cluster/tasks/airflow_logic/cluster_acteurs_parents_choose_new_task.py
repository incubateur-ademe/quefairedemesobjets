import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.business_logic import cluster_acteurs_choose_new_parents
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_parents_choose_new_task"
    ============================================================

    💡 quoi: sélection du parent d'un cluster

    🎯 pourquoi: car c'est la finalité du clustering: choisir 1
    parent pour y rattacher tous les autres acteurs du cluster

    🏗️ comment: selon la logique suivant
     - parents existant avec le plus d'enfant
     - génération d'un nouveau parent si pas de parent existant
    """


def cluster_acteurs_parents_choose_new_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    config: ClusterConfig = kwargs["ti"].xcom_pull(
        key="config", task_ids="cluster_acteurs_config_create"
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids="cluster_acteurs_suggestions_display"
    )
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    log.preview("config reçue", config)
    log.preview("acteurs groupés", df)

    df = cluster_acteurs_choose_new_parents(df)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("acteurs avec parents sélectionnés", df)

    # Les XCOM étant spécifiques à une tâche on peut pousser
    # le même nom sans risque de collision. Ainsi, pousse le nom "df"
    # et pas "df_norm" pour avoir toujours le nom "df" à travers
    # toutes les tâches et pas avoir à se rappeler de la nomenclature
    # des tâches précédentes.
    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_parents_choose_new_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_parents_choose_new",
        python_callable=cluster_acteurs_parents_choose_new_wrapper,
        dag=dag,
    )
