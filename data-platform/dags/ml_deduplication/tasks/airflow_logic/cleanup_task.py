"""Tâche Airflow de nettoyage (suppression de la table temporaire d'acteurs)"""

import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.task.trigger_rule import TriggerRule
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_pull
from ml_deduplication.tasks.business_logic.ml_deduplication_cleanup import (
    ml_deduplication_cleanup,
)

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CLEANUP}"
    ============================================================

    💡 quoi: supprime la table temporaire du pool d'acteurs créée pour ce run

    🎯 pourquoi: éviter d'accumuler des tables temporaires dans le warehouse

    🏗️ comment: drop de la table (idempotent) si un run_id est connu
    """


def ml_deduplication_cleanup_wrapper(ti) -> None:
    logger.info(task_info_get())
    run_id: str | None = xcom_pull(ti, XCOMS.RUN_ID)
    ml_deduplication_cleanup(run_id)


def ml_deduplication_cleanup_task() -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CLEANUP,
        python_callable=ml_deduplication_cleanup_wrapper,
        trigger_rule=TriggerRule.ALL_DONE,
    )
