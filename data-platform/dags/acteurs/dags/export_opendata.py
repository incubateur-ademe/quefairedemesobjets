from acteurs.tasks.airflow_logic.export_opendata_csv_to_s3_task import (
    export_opendata_csv_to_s3_task,
)
from acteurs.tasks.airflow_logic.remove_old_s3_opendata_csv_task import (
    remove_old_s3_opendata_csv_task,
)
from airflow import DAG
from decouple import config
from shared.config.airflow import DEFAULT_ARGS
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

ENVIRONMENT = config("ENVIRONMENT", default="development")


with DAG(
    "export_opendata_dag",
    default_args=DEFAULT_ARGS,
    schedule=SCHEDULES.EVERY_MONDAY_AT_01_00,
    start_date=START_DATES.DEFAULT,
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
        "opendata_table": "exposure_opendata_acteur",
    },
    max_active_runs=1,
) as dag:

    export_opendata_csv_to_s3_task(dag=dag) >> remove_old_s3_opendata_csv_task(dag=dag)
