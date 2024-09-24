from datetime import datetime, timedelta
from pathlib import Path

import decouple
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2022, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

ENVIRONMENT = decouple.config("ENVIRONMENT", "development")

with DAG(
    "download_dags_from_s3",
    default_args=default_args,
    description="DAG to download dags from S3",
    schedule_interval=timedelta(minutes=5),
    catchup=False,
) as dag:

    root_path = Path(__file__).resolve().parent.parent
    if ENVIRONMENT != "development":

        download_dags = BashOperator(
            task_id="download_dags_from_s3",
            bash_command=f"{root_path}/sync_dags.sh ",
            dag=dag,
        )
