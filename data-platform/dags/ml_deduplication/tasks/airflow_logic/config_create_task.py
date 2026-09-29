"""Tâche Airflow pour créer la configuration ML-déduplication + run_id"""

import logging

from airflow.providers.standard.operators.python import PythonOperator
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.config.xcoms import XCOMS, xcom_push
from ml_deduplication.tasks.business_logic.ml_deduplication_config_create import (
    ml_deduplication_config_create,
    ml_deduplication_run_id_generate,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CONFIG_CREATE}"
    ============================================================

    💡 quoi: valide la configuration fournie par la UI (+ défauts si il y en a)
        et génère le run_id partagé par toutes les tâches du run

    🎯 pourquoi: échouer au plus tôt si il y a des problèmes de conf et ne pas
        faire du traitement de données inutile. Le run_id doit être identique
        entre l'inférence (qui l'écrit dans les tables de sortie) et la
        sélection des clusters (qui filtre ces tables par run_id).

    🏗️ comment: en comparant la config fournie avec des règles censées
        s'aligner avec les besoins métier (ex: prérequis)
        et la UI (ex: optionalité)
    """


def ml_deduplication_config_create_wrapper(ti, params, dag_run, fields_all) -> None:
    """Wrapper de la tâche Airflow pour créer une configuration à
    partir des params du DAG + autre logique métier / valeurs DB."""
    logger.info(task_info_get())

    run_id = ml_deduplication_run_id_generate(dag_run.run_id)
    config = ml_deduplication_config_create(params, dag_run.run_id, fields_all)

    log.preview("Config", config)
    log.preview("run_id", run_id)

    xcom_push(ti, XCOMS.CONFIG, config)
    xcom_push(ti, XCOMS.RUN_ID, run_id)


def ml_deduplication_config_create_task(
    fields_all: list[str],
) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CONFIG_CREATE,
        python_callable=ml_deduplication_config_create_wrapper,
        op_kwargs={"fields_all": fields_all},
    )
