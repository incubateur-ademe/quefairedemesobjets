"""Tâche Airflow pour supprimer le fichier temporaire en fin de DAG"""

from pathlib import Path
from shutil import rmtree

from airflow.sdk import task
from airflow.task.trigger_rule import TriggerRule
from utils import logging_utils as log


def task_info_get():
    return "#### Nettoyage du fichier temporaire contenant les données OSM"


@task(
    doc_md=task_info_get(),
    # Run the cleanup even if the upstream tasks failed: the temporary
    # directory is created with delete=False and must not stay on disk.
    trigger_rule=TriggerRule.ALL_DONE,
)
def osm_dataset_cleanup_task(
    tmp_filepath: str | None,
) -> None:
    logger = log.logger_get()

    # If the download failed, no file path was produced.
    if tmp_filepath is None:
        logger.info("Nothing to clean: no dataset file was produced")
        return

    dataset_directory = Path(tmp_filepath).parent
    if not dataset_directory.exists():
        logger.info("Nothing to clean: %s already removed", tmp_filepath)
        return

    logger.info("Preparing to delete %s", tmp_filepath)
    rmtree(dataset_directory)
    logger.info("Successfuly deleted %s", tmp_filepath)
