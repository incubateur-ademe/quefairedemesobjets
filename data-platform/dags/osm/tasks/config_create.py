"""Tâche Airflow pour créer la configuration OSM Extract and load"""

from airflow.sdk import ParamsDict, task
from osm.config.models import OSMExtractLoadConfig
from utils import logging_utils as log


def task_info_get():
    return "# Valide la configuration fournie par l'UI"


@task(doc_md=task_info_get())
def osm_extract_load_config_create_task(
    params: ParamsDict = None,
) -> OSMExtractLoadConfig:
    config = OSMExtractLoadConfig(**params)

    log.preview("Config", config)

    return config
