import logging
import subprocess
import tempfile
from pathlib import Path
from typing import TextIO

import pendulum
from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from shared.config.airflow import TMP_FOLDER
from shared.psql.utils import psql_env_from_dsn

logger = logging.getLogger(__name__)

MAIN_OPENDATA_FILENAME = "acteurs.csv"


def run_psql_safely(dsn: str, cmd: str, stdout: TextIO) -> None:
    try:
        subprocess.run(
            ["psql", "-c", cmd],
            env=psql_env_from_dsn(dsn),
            check=True,
            stdout=stdout,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"psql failed with exit code {exc.returncode}") from None


def export_opendata_csv_to_s3(export_opendata_config: ExportOpendataConfig):

    from utils.django import django_setup_full

    django_setup_full()
    from django.conf import settings

    with tempfile.TemporaryDirectory(dir=TMP_FOLDER) as temp_dir:
        timestamp = pendulum.now("UTC").strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}.csv"
        permatent_filename = MAIN_OPENDATA_FILENAME
        tempfile_path = Path(temp_dir, filename)
        with open(tempfile_path, "w") as f:
            run_psql_safely(
                settings.DB_WAREHOUSE,
                (
                    "COPY "
                    f"{export_opendata_config.opendata_table} "
                    "TO STDOUT WITH CSV HEADER"
                ),
                f,
            )

        if not Path(tempfile_path).exists():
            raise Exception(f"File {tempfile_path} does not exist")

        S3Hook(aws_conn_id=export_opendata_config.s3_connection_id).load_file(
            filename=tempfile_path,
            key=str(Path(export_opendata_config.remote_dir, filename)),
            bucket_name=export_opendata_config.bucket_name,
        )
        S3Hook(aws_conn_id=export_opendata_config.s3_connection_id).load_file(
            filename=tempfile_path,
            key=str(Path(export_opendata_config.remote_dir, permatent_filename)),
            bucket_name=export_opendata_config.bucket_name,
            replace=True,
            acl_policy="public-read",
        )
