"""
Tâche Airflow pour créer la configuration de clustering
"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from cluster.config.models import ClusterConfig
from cluster.config.tasks import TASKS
from cluster.tasks.business_logic.cluster_acteurs_config_create import (
    cluster_acteurs_config_create,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASKS.CONFIG_CREATE}"
    ============================================================

    💡 quoi: valide la configuration fournie par la UI (+ défauts si il y en a)

    🎯 pourquoi: échouer au plus tôt si il y a des problèmes de conf et ne pas
        faire du traitement de données inutile

    🏗️ comment: en comparant la config fournie avec des règles censées
        s'aligner avec les besoins métier (ex: prérequis)
        et la UI (ex: optionalité)
    """


def cluster_acteurs_config_create_wrapper(ti, params):
    """Wrapper de la tâche Airflow pour créer une configuration à
    partir des params du DAG + autre logique métier / valeurs DB."""
    logger.info(task_info_get())
    config: ClusterConfig = cluster_acteurs_config_create(params)
    log.preview("Config", config)


def cluster_acteurs_config_create_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CONFIG_CREATE,
        python_callable=cluster_acteurs_config_create_wrapper,
        dag=dag,
    )
