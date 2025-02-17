import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import (
    TASK_CLUSTERS_DISPLAY,
    TASK_CONFIG_CREATE,
    TASK_PARENTS_CHOOSE_NEW,
)
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    cluster_acteurs_parents_choose_new,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_PARENTS_CHOOSE_NEW}"
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
        key="config", task_ids=TASK_CONFIG_CREATE
    )
    df: pd.DataFrame = kwargs["ti"].xcom_pull(key="df", task_ids=TASK_CLUSTERS_DISPLAY)
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    log.preview("config reçue", config)
    log.preview("acteurs groupés", df)

    df = cluster_acteurs_parents_choose_new(df)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(
        "clusters avec parents sélectionnés", df, groupby="cluster_id"
    )

    kwargs["ti"].xcom_push(key="df", value=df)


def cluster_acteurs_parents_choose_new_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_PARENTS_CHOOSE_NEW,
        python_callable=cluster_acteurs_parents_choose_new_wrapper,
        dag=dag,
    )
