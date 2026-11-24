"""Tâche Airflow pour créer la configuration OSM Extract and load"""

from pathlib import Path
from shutil import rmtree

from airflow.sdk import task
from utils import logging_utils as log


def task_info_get():
    return "#### Nettoyage du fichier temporaire contenant les données OSM"


@task(doc_md=task_info_get())
def osm_dataset_cleanup_task(
    tmp_filepath: str,
) -> None:
    log.logger_get().info("Preparing to delete %s", tmp_filepath)

    rmtree(Path(tmp_filepath).parent)

    log.logger_get().info("Successfuly deleted %s", tmp_filepath)
