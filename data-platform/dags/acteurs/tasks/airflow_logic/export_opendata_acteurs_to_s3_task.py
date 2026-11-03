"""Performs crawl checks on the URLs"""

import logging

from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from acteurs.tasks.business_logic.export_opendata_csv_to_s3 import (
    export_opendata_csv_to_s3,
)
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from utils import logging_utils as log

logger = logging.getLogger(__name__)

TASK_NAME = "export_opendata_acteurs_to_s3"


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASK_NAME}"
    ============================================================
    💡 quoi: Extraire les données de la table exposure_opendata_acteur en CSV
    et exporter le fichier CSV vers S3

    🎯 pourquoi: Mettre à jour régulièrement les données des acteurs en open-data

    🏗️ comment: Export des données en command bash dans un fichier temporaire
    et enregistrement dans le bucket S3
    """


def export_opendata_acteurs_to_s3_wrapper(ti, params) -> None:
    logger.info(task_info_get())
    export_opendata_config = ExportOpendataConfig(**params)

    log.preview("paramètres du DAG", export_opendata_config)
    export_opendata_csv_to_s3(export_opendata_config=export_opendata_config)


def export_opendata_acteurs_to_s3_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_NAME,
        python_callable=export_opendata_acteurs_to_s3_wrapper,
        dag=dag,
    )
