"""Tâche Airflow de sélection du parent d'un cluster (ML-déduplication)"""

import logging

import pandas as pd
from airflow.providers.standard.operators.python import PythonOperator
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    cluster_acteurs_parents_choose_new,
)
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_pull, xcom_push
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


def ml_deduplication_parents_choose_new_wrapper(ti) -> None:
    logger.info(task_info_get())

    config: MLDeduplicationConfig = xcom_pull(ti, XCOMS.CONFIG)
    df: pd.DataFrame = xcom_pull(ti, XCOMS.DF_CLUSTERS_SELECT)

    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("df vide: on devrait pas être là")

    log.preview("config reçue", config)
    log.preview("acteurs clusterisés", df)

    df = cluster_acteurs_parents_choose_new(df)

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown(
        "clusters avec parents sélectionnés", df, groupby="cluster_id"
    )

    xcom_push(ti, XCOMS.DF_PARENTS_CHOOSE_NEW, df)


def ml_deduplication_parents_choose_new_task() -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.PARENTS_CHOOSE_NEW,
        python_callable=ml_deduplication_parents_choose_new_wrapper,
    )
