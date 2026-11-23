"""Tâche Airflow pour créer la configuration OSM Extract and load"""

import logging

from airflow.sdk import ParamsDict, task
from osm.config.models import OSMExtractLoadConfig
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return """
    💡 quoi: valide la configuration fournie par la UI (+ défauts si il y en a)
        et génère le run_id partagé par toutes les tâches du run

    🎯 pourquoi: échouer au plus tôt si il y a des problèmes de conf et ne pas
        faire du traitement de données inutile. Le run_id doit être identique
        entre l'inférence (qui l'écrit dans les tables de sortie) et la
        sélection des clusters (qui filtre ces tables par run_id).

    🏗️ comment: en comparant la config fournie avec des règles censées
        s'aligner avec les besoins métier (ex: prérequis)
        et la UI (ex: optionalité)
    """


@task(doc_md=task_info_get())
def osm_extract_load_config_create_task(
    params: ParamsDict = None,
) -> OSMExtractLoadConfig:
    config = OSMExtractLoadConfig(**params)

    log.preview("Config", config)

    return config
