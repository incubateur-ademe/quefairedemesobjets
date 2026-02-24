import logging

import pandas as pd
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.config.tasks import TASKS
from cluster.config.xcoms import XCOMS, xcom_pull
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    cluster_acteurs_parents_choose_new,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.PARENTS_CHOOSE_NEW}"
    ============================================================

    💡 quoi: sélection du parent d'un cluster

    🎯 pourquoi: car c'est la finalité du clustering: choisir 1
    parent pour y rattacher tous les autres acteurs du cluster

    🏗️ comment: selon la logique suivant
     - parents existant avec le plus d'enfant
     - génération d'un nouveau parent si pas de parent existant
    """


def cluster_acteurs_parents_choose_new_wrapper(ti) -> None:
    logger.info(task_info_get())

    # use xcom to get the params from the previous task
    config: ClusterConfig = xcom_pull(ti, XCOMS.CONFIG)
    df: pd.DataFrame = xcom_pull(ti, XCOMS.DF_CLUSTERS_PREPARE)

    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("df vide: on devrait pas être là")

    log.preview("config reçue", config)
    log.preview("acteurs clusterisés", df)

    df = cluster_acteurs_parents_choose_new(df)

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(
        "clusters avec parents sélectionnés", df, groupby="cluster_id"
    )

    ti.xcom_push(key=XCOMS.DF_PARENTS_CHOOSE_NEW, value=df)


def cluster_acteurs_parents_choose_new_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.PARENTS_CHOOSE_NEW,
        python_callable=cluster_acteurs_parents_choose_new_wrapper,
        dag=dag,
    )
