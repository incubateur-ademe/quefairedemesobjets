"""Generic task to create configuration"""

import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from enrich.config.models import EnrichActeursClosedConfig
from enrich.config.tasks import TASKS

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.CONFIG_CREATE}"
    ============================================================
    💡 quoi: création de la config

    🎯 pourquoi: s'assurer qu'elle est OK avant de faire du travail,
    réutiliser la config pour les autres tâches

    🏗️ comment: on ingère les paramètres Airflow dans un modèle pydantic
    """


def enrich_config_create_wrapper(ti, dag, params) -> None:
    logger.info(task_info_get())

    config = EnrichActeursClosedConfig(**params)
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")


def enrich_config_create_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.CONFIG_CREATE,
        python_callable=enrich_config_create_wrapper,
        dag=dag,
        doc_md="📖 **Création de la config**",
    )
