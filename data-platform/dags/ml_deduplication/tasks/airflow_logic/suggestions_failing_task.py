"""Tâche Airflow d'affichage des suggestions échouées (ML-déduplication)"""

import logging

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowFailException, AirflowSkipException
from airflow.task.trigger_rule import TriggerRule
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_pull
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.SUGGESTIONS_FAILING}"
    ============================================================

    💡 quoi: affichage des suggestions échouées (si présentes)

    🎯 pourquoi: avoir une tâche clairement en état d'échec
    dans Airflow (MAIS après l'écriture des suggestions réussies
    en DB pour) pour pas passer à côté d'erreurs tout en évitant
    les blocages.

    🏗️ comment: on récupère les suggestions échouées de la tâche
    précédente, si elles existent, et on les affiche, sinon on
    soulève SkipException pour expliciter l'absence d'erreur
    """


def ml_deduplication_suggestions_failing_wrapper(ti) -> None:
    logger.info(task_info_get())

    failing: list[dict] = xcom_pull(ti, XCOMS.SUGGESTIONS_FAILING)

    if not failing:
        raise AirflowSkipException("Pas de suggestions échouées")

    for suggestion in failing:
        msg = f"🔴 Erreur sur cluster_id={suggestion['cluster_id']} 🔴"
        log.preview(msg, suggestion["error"])
    raise AirflowFailException("Voir suggestions de clusters échouées ci-dessus")


def ml_deduplication_suggestions_failing_task() -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.SUGGESTIONS_FAILING,
        python_callable=ml_deduplication_suggestions_failing_wrapper,
        trigger_rule=TriggerRule.ALL_DONE,
    )
