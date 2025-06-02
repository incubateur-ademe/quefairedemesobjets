import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

logger = logging.getLogger(__name__)


def export_opendata_csv_to_s3(export_opendata_config: ExportOpendataConfig):
    with tempfile.TemporaryDirectory() as temp_dir:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}.csv"
        permatent_filename = "acteurs.csv"
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
                    f"COPY {export_opendata_config.opendata_schema}."
                    f"{export_opendata_config.opendata_table}"
                    " TO STDOUT WITH CSV HEADER",
                ],
                env={"PGPASSWORD": os.environ.get("POSTGRES_PASSWORD") or ""},
                check=True,
                stdout=f,
                text=True,
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
