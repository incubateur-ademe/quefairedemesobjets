import logging

from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from acteurs.tasks.business_logic.export_opendata_fiches_to_s3 import (
    FICHES_OPENDATA_FILENAMES,
    export_opendata_fiche_to_s3,
)
from acteurs.tasks.business_logic.remove_old_s3_opendata_csv import (
    remove_old_s3_opendata_csv,
)
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get(task_name: str, filename: str) -> str:
    return f"""
    ============================================================
    Description de la tâche "{task_name}"
    ============================================================
    💡 quoi: Publier {filename}, open data des fiches objets et déchets du CMS,
    sur S3

    🎯 pourquoi: Mettre à jour régulièrement les consignes en open-data

    🏗️ comment: Le fichier est servi par l'API v1 de la webapp
    (/api/v1/{filename}) et copié dans le bucket S3 : une copie datée, et le
    fichier non daté comme dernier état
    """


def _export_task(dag: DAG, filename: str) -> PythonOperator:
    task_name = f"export_opendata_{filename.removesuffix('.csv')}_to_s3"

    def wrapper(ti, params) -> None:
        logger.info(task_info_get(task_name, filename))
        export_opendata_config = ExportOpendataConfig(**params)
        log.preview("paramètres du DAG", export_opendata_config)
        export_opendata_fiche_to_s3(export_opendata_config, filename)

    return PythonOperator(task_id=task_name, python_callable=wrapper, dag=dag)


def export_opendata_produits_to_s3_task(dag: DAG) -> PythonOperator:
    return _export_task(dag, "produits.csv")


def export_opendata_consignes_to_s3_task(dag: DAG) -> PythonOperator:
    return _export_task(dag, "consignes.csv")


def remove_old_s3_opendata_fiches_wrapper(ti, params) -> None:
    export_opendata_config = ExportOpendataConfig(**params)
    log.preview("paramètres du DAG", export_opendata_config)
    remove_old_s3_opendata_csv(
        export_opendata_config,
        remote_dir=export_opendata_config.fiches_remote_dir,
        kept_filenames=FICHES_OPENDATA_FILENAMES,
    )


def remove_old_s3_opendata_fiches_task(dag: DAG) -> PythonOperator:
    return PythonOperator(
        task_id="remove_old_s3_opendata_fiches",
        python_callable=remove_old_s3_opendata_fiches_wrapper,
        dag=dag,
    )
