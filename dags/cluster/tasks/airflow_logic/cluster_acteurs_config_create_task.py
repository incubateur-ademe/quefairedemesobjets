"""
Tâche Airflow pour valider la configuration de clustering
"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.task_ids import TASK_CONFIG_CREATE
from cluster.tasks.business_logic.cluster_acteurs_config_create import (
    cluster_acteurs_config_create,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_CONFIG_CREATE}"
    ============================================================

    💡 quoi: valide la configuration fournie par la UI (+ défauts si il y en a)

    🎯 pourquoi: échouer au plus tôt si il y a des problèmes de conf et ne pas
        faire du traitement de données inutile

    🏗️ comment: en comparant la config fournie avec des règles censées
        s'aligner avec les besoins métier (ex: prérequis)
        et la UI (ex: optionalité)
    """


def cluster_acteurs_config_create_wrapper(**kwargs):
    """Wrapper de la tâche Airflow pour créer une configuration à
    partir des params du DAG + autre logique métier / valeurs DB."""
    logger.info(task_info_get())
    config: ClusterConfig = cluster_acteurs_config_create(kwargs["params"])
    log.preview("Config", config)
    kwargs["ti"].xcom_push(key="config", value=config)


def cluster_acteurs_config_create_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id=TASK_CONFIG_CREATE,
        python_callable=cluster_acteurs_config_create_wrapper,
        dag=dag,
    )
