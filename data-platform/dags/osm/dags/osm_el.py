"""DAG that extract OSM data from https://download.geofabrik.de/europe/france/
and load a subset of the dataset into the datawarehouse.
"""

from airflow.sdk import Param, dag
from decouple import config
from osm.tasks.airflow_logic.config_create_task import (
    osm_extract_load_config_create_task,
)
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

DAG_ID = "osm_extract_load"
ENVIRONMENT = config("ENVIRONMENT", default="development")

PARAMS = {
    "dry_run": Param(
        False,
        type="boolean",
        description_md="""
                🚱 Si coché, aucune tâche d'écriture ne sera effectuée.
                Ceci permet de tester le DAG rapidement sans peur de
                casser quoi que ce soit (itérer plus vite)
                (ex: pas d'écriture des suggestions en DB,
                donc pas visible dans Django Admin).""",
    ),
    "output_table": Param(
        "public.osm_elements",
        type="string",
        description_md="""Base name of the DB table(s) to upload results to, in the
            `public` schema of the warehouse DB. Clusters go to
            `<output_table>_clusters`, candidate pairs to
            `<output_table>_predictions`. Required for the post-inference
            suggestion logic.""",
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

    osm_extract_load_config_create_task()


osm_extract_load_dag = osm_extract_load()

if __name__ == "__main__":
    osm_extract_load_dag.test()
