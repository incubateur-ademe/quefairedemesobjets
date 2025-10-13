"""Performs crawl checks on the URLs"""

import logging

from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from acteurs.tasks.business_logic.remove_old_s3_opendata_csv import (
    remove_old_s3_opendata_csv,
)
from airflow import DAG
from airflow.operators.python import PythonOperator
from utils import logging_utils as log

logger = logging.getLogger(__name__)

TASK_NAME = "remove_old_s3_opendata_csv"


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASK_NAME}"
    ============================================================
    💡 quoi: Supprimer les fichiers anciens de S3

    🎯 pourquoi: Nettoyer le bucket S3

    🏗️ comment: Utilisation d'une commande S3 pour supprimer les fichiers
    vieux de plus de 30 jours
    """


def remove_old_s3_opendata_csv_wrapper(ti, params) -> None:
    logger.info(task_info_get())
    export_opendata_config = ExportOpendataConfig(**params)

    log.preview("paramètres du DAG", export_opendata_config)
    remove_old_s3_opendata_csv(export_opendata_config=export_opendata_config)


def remove_old_s3_opendata_csv_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_NAME,
        python_callable=remove_old_s3_opendata_csv_wrapper,
        dag=dag,
    )
