"""Tâche Airflow de sélection/enrichissement des clusters issus de l'inférence"""

import logging

import pandas as pd
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_pull, xcom_push
from ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select import (
    ml_deduplication_clusters_select,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CLUSTERS_SELECT}"
    ============================================================

    💡 quoi: récupère les clusters produits par l'inférence ML pour le
        run_id courant (table <output_table>_clusters), y joint les acteurs
        complets et les enrichit comme le fait clusters_prepare du DAG de
        clustering (parent_id, enfants des parents, filtrage, tri)

    🎯 pourquoi: les tâches en aval (choix du parent, enrichissement,
        suggestions) sont réutilisées telles quelles depuis le DAG de
        clustering et attendent ce format de df

    🏗️ comment: lecture des clusters en base (warehouse), jointure avec
        les acteurs, puis enrichissement
    """


def ml_deduplication_clusters_select_wrapper(ti) -> None:
    logger.info(task_info_get())

    config: MLDeduplicationConfig = xcom_pull(ti, XCOMS.CONFIG)
    run_id: str = xcom_pull(ti, XCOMS.RUN_ID)
    log.preview("Config reçue", config)
    log.preview("run_id", run_id)

    df = ml_deduplication_clusters_select(config, run_id)

    if not isinstance(df, pd.DataFrame) or df.empty:
        msg = "Pas de clusters trouvés pour ce run, on s'arrête là"
        raise AirflowSkipException(msg)

    xcom_push(ti, XCOMS.DF_CLUSTERS_SELECT, df)


def ml_deduplication_clusters_select_task() -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CLUSTERS_SELECT,
        python_callable=ml_deduplication_clusters_select_wrapper,
    )
