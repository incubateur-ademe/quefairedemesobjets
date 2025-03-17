import logging
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG

# from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 14),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

BUCKET_NAME = "lvao-data-source"
REMOTE_DIR = "opendata"
S3_CONNECTION_ID = "s3data"
OPENDATA_TABLE = "exposure_opendata_acteur"


logger = logging.getLogger(__name__)


def copy_to_s3():
    s3_hook = S3Hook(aws_conn_id=S3_CONNECTION_ID)
    s3_hook.load_file(
        filename="/opt/airflow/tmp/opendata.csv",
        key=Path(REMOTE_DIR, "opendata.csv"),
        bucket_name=BUCKET_NAME,
    )


def export_opendata_csv_to_s3():
    with tempfile.TemporaryDirectory() as temp_dir:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"opendata_{timestamp}.csv"
        tempfile_path = Path(temp_dir, filename)
        with open(tempfile_path, "w") as f:
            subprocess.run(
                [
                    "psql",
                    "-h",
                    os.environ.get("POSTGRES_HOST") or "",
                    "-p",
                    os.environ.get("POSTGRES_PORT") or "",
                    "-U",
                    os.environ.get("POSTGRES_USER") or "",
                    "-d",
                    os.environ.get("POSTGRES_DB") or "",
                    "-c",
                    f"COPY {OPENDATA_TABLE} TO STDOUT WITH CSV HEADER",
                ],
                env={"PGPASSWORD": os.environ.get("POSTGRES_PASSWORD") or ""},
                check=True,
                stdout=f,
                text=True,
            )

        if not Path(tempfile_path).exists():
            raise Exception(f"File {tempfile_path} does not exist")

        S3Hook(aws_conn_id=S3_CONNECTION_ID).load_file(
            filename=tempfile_path,
            key=str(Path(REMOTE_DIR, filename)),
            bucket_name=BUCKET_NAME,
        )


with DAG(
    "export_opendata_dag",
    default_args=default_args,
    dag_display_name="Exporter les Acteurs en Open-Data",
    description=(
        "Ce DAG export les acteurs disponibles en opendata précédemment générés dans la"
        " table `exposure_opendata_acteur` de la base de données."
    ),
    schedule=None,
    max_active_runs=1,
) as dag:

    # Solution 1: only 1 task
    PythonOperator(
        task_id="export_opendata_csv_to_s3",
        python_callable=export_opendata_csv_to_s3,
        dag=dag,
    )

    # Solution 2: 2 tasks
    # export_to_csv_task = BashOperator(
    #     task_id="export_to_csv",
    #     bash_command=(
    #         "mkdir -p /opt/airflow/tmp && "
    #         "cd /opt/airflow/tmp && "
    #         "PGPASSWORD=$POSTGRES_PASSWORD "
    #       "psql -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB"
    #         ' -c "COPY exposure_opendata_acteur TO STDOUT WITH CSV HEADER"'
    #         " > opendata.csv"
    #     ),
    #     dag=dag,
    # )

    # copy_to_s3_task = PythonOperator(
    #     task_id="copy_to_s3",
    #     python_callable=copy_to_s3,
    #     dag=dag,
    # )

    # export_to_csv_task >> copy_to_s3_task
