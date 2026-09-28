import logging

from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from acteurs.tasks.business_logic.export_opendata_fiches_to_s3 import (
    export_opendata_fiches_to_s3,
)
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from utils import logging_utils as log

logger = logging.getLogger(__name__)

TASK_NAME = "export_opendata_fiches_to_s3"


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASK_NAME}"
    ============================================================
    💡 quoi: Publier produits.csv et consignes.csv, l'open data des fiches
    objets et déchets du CMS, sur S3

    🎯 pourquoi: Mettre à jour régulièrement les consignes en open-data

    🏗️ comment: Les fichiers sont servis par l'API v1 de la webapp
    (/api/v1/produits.csv, /api/v1/consignes.csv) et copiés dans le bucket S3
    """


def export_opendata_fiches_to_s3_wrapper(ti, params) -> None:
    logger.info(task_info_get())
    export_opendata_config = ExportOpendataConfig(**params)

    log.preview("paramètres du DAG", export_opendata_config)
    export_opendata_fiches_to_s3(export_opendata_config=export_opendata_config)


def export_opendata_fiches_to_s3_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id=TASK_NAME,
        python_callable=export_opendata_fiches_to_s3_wrapper,
        dag=dag,
    )
