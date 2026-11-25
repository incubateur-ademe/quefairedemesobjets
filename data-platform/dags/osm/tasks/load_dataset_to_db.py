"""Tâche Airflow qui télécharge dans un dossier temporaire le dataset OSM"""

import os
from pathlib import Path

from airflow.sdk import task
from psycopg import conninfo


def task_info_get():
    return """#### Chargement dans le datawarehouse (table `public.base_osm`)
    des données OSM."""


OSM2PGSQL_CONFIG_FILEPATH = (
    Path(__file__).parent.parent / "config" / "osm_2_pgsql.lua"
).absolute()  # The LUA file lives in the config path
WAREHOUSE_CON_INFO = conninfo.conninfo_to_dict(os.environ["DB_WAREHOUSE"])


@task.bash(
    doc_md=task_info_get(),
    env={
        "PGHOST": WAREHOUSE_CON_INFO["host"],
        "PGPORT": str(WAREHOUSE_CON_INFO["port"]),
        "PGDATABASE": WAREHOUSE_CON_INFO["dbname"],
        "PGUSER": WAREHOUSE_CON_INFO["user"],
        "PGPASSWORD": WAREHOUSE_CON_INFO["password"],
    },  # type: ignore
)
def load_dataset_to_db_task(
    osm_filepath: str,
) -> str:

    bash_command = (
        "osm2pgsql --create --output=flex -S "
        f"{OSM2PGSQL_CONFIG_FILEPATH} {osm_filepath}"
    )

    return bash_command
