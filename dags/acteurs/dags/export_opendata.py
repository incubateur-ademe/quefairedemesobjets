from datetime import timedelta

import pendulum
from acteurs.tasks.airflow_logic.export_opendata_csv_to_s3_task import (
    export_opendata_csv_to_s3_task,
)
from airflow import DAG
from decouple import config
from shared.config.schedules import SCHEDULES
from shared.config.tags import TAGS

ENVIRONMENT = config("ENVIRONMENT", default="development")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": pendulum.today("UTC").add(days=-1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    "export_opendata_dag",
    default_args=default_args,
    dag_display_name="Acteurs Open-Data - Exporter les Acteurs en Open-Data",
    description=(
        "Ce DAG export les acteurs disponibles en opendata précédemment générés dans la"
        " table `exposure_opendata_acteur` de la base de données."
    ),
    tags=[TAGS.COMPUTE, TAGS.EXPORT, TAGS.ACTEURS, TAGS.OPENDATA, TAGS.S3],
    params={
        "bucket_name": "lvao-opendata",
        "remote_dir": "acteurs" if ENVIRONMENT == "prod" else f"acteurs-{ENVIRONMENT}",
        "s3_connection_id": "s3data",
        "opendata_schema": "warehouse",
        "opendata_table": "exposure_opendata_acteur",
    },
    schedule=SCHEDULES.WEEKLY_AT_1AM,
    max_active_runs=1,
) as dag:

    export_opendata_csv_to_s3_task(dag=dag)
