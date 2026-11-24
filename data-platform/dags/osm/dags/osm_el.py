"""DAG that extract OSM data from https://download.geofabrik.de/europe/france/
and load a subset of the dataset into the datawarehouse.
"""

from airflow.sdk import Param, dag
from decouple import config
from osm.tasks.config_create import (
    osm_extract_load_config_create_task,
)
from osm.tasks.download_dataset import download_osm_dataset_task
from osm.tasks.load_dataset_to_db import load_dataset_to_db_task
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

DAG_ID = "osm_extract_load"
ENVIRONMENT = config("ENVIRONMENT", default="development")

PARAMS = {
    "dry_run": Param(
        False,
        type="boolean",
        description_md="""Si coché, aucune tâche d'écriture ne sera effectuée.
                Ceci permet de tester le DAG rapidement sans peur de
                casser quoi que ce soit (itérer plus vite)
                (ex: pas d'écriture des suggestions en DB,
                donc pas visible dans Django Admin).""",
    ),
    "osm_dataset_url": Param(
        "https://download.geofabrik.de/europe/france/france-latest.osm.pbf",
        type="string",
        description_md="""URL du dataset sur le site [Geofabrik](https://download.geofabrik.de/europe/france/)""",
    ),
}


@dag(
    dag_id=DAG_ID,
    dag_display_name="OSM - Extract and Load",
    schedule=SCHEDULES.EVERY_FIRST_DAY_OF_MONTH_AT_02_00,
    start_date=START_DATES.DEFAULT,
    is_paused_upon_creation=False,
    max_active_runs=1,
    catchup=False,
    tags=[
        TAGS.OSM,
    ],
    params=PARAMS,
)
def osm_extract_load():

    config = osm_extract_load_config_create_task()

    osm_dataset_filepath = download_osm_dataset_task(config)

    load_dataset_to_db_task(osm_dataset_filepath)


osm_extract_load_dag = osm_extract_load()

if __name__ == "__main__":
    osm_extract_load_dag.test()
