from datetime import datetime, timedelta

from acteurs.tasks.airflow_logic.export_opendata_csv_to_s3_task import (
    export_opendata_csv_to_s3_task,
)
from airflow import DAG

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 14),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    "export_opendata_dag",
    default_args=default_args,
    dag_display_name="Exporter les Acteurs en Open-Data",
    description=(
        "Ce DAG export les acteurs disponibles en opendata précédemment générés dans la"
        " table `exposure_opendata_acteur` de la base de données."
    ),
    params={
        "bucket_name": "lvao-opendata",
        "remote_dir": "acteurs",
        "s3_connection_id": "s3data",
        "opendata_table": "exposure_opendata_acteur",
    },
    schedule=None,
    max_active_runs=1,
) as dag:

    export_opendata_csv_to_s3_task(dag=dag)
