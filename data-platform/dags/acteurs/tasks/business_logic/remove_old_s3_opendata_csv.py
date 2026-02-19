import logging

import pendulum
from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from acteurs.tasks.business_logic.export_opendata_csv_to_s3 import (
    MAIN_OPENDATA_FILENAME,
)
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

logger = logging.getLogger(__name__)


def remove_old_s3_opendata_csv(export_opendata_config: ExportOpendataConfig):
    # Récupérer la liste des fichiers existants dans le répertoire
    s3_hook = S3Hook(aws_conn_id=export_opendata_config.s3_connection_id)
    older_than_one_month_files = s3_hook.list_keys(
        bucket_name=export_opendata_config.bucket_name,
        prefix=export_opendata_config.remote_dir,
        to_datetime=pendulum.now("UTC").subtract(days=30),
    )
    older_than_one_month_files = [
        f for f in older_than_one_month_files if not f.endswith(MAIN_OPENDATA_FILENAME)
    ]
    logger.warning(f"🟠 Suppression des fichiers: {older_than_one_month_files}")
    if older_than_one_month_files:
        s3_hook.delete_objects(
            bucket=export_opendata_config.bucket_name,
            keys=older_than_one_month_files,
        )
