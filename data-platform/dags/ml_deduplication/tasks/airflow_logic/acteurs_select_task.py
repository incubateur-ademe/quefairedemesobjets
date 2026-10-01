"""Tâche Airflow de sélection des acteurs + création de la table temporaire"""

import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_pull, xcom_push
from ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select import (
    ml_deduplication_acteurs_select,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SELECTION}"
    ============================================================

    💡 quoi: va chercher en base de données les acteurs correspondants
        aux critères d'inclusion et d'exclusion du DAG et les écrit dans
        une table temporaire du warehouse (le pool donné à l'inférence ML)

    🎯 pourquoi: c'est la donnée de base sur laquelle l'inférence ML va
        tourner (via --acteurs-table)

    🏗️ comment: constructions/execution d'une requête SQL sur la base
        des critères d'inclusion/exclusion puis écriture dans une table
        temporaire
    """


def ml_deduplication_acteurs_select_wrapper(ti) -> None:
    logger.info(task_info_get())

    config: MLDeduplicationConfig = xcom_pull(ti, XCOMS.CONFIG)
    run_id: str = xcom_pull(ti, XCOMS.RUN_ID)
    log.preview("Config reçue", config)
    log.preview("run_id", run_id)

    df, table_name = ml_deduplication_acteurs_select(config, run_id)

    if df.empty:
        raise AirflowSkipException("Aucun acteur sélectionné, on s'arrête là")

    log.preview("table temporaire du pool d'acteurs", table_name)
    xcom_push(ti, XCOMS.ACTEURS_VIEW, table_name)


def ml_deduplication_acteurs_select_task() -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SELECTION,
        python_callable=ml_deduplication_acteurs_select_wrapper,
    )
