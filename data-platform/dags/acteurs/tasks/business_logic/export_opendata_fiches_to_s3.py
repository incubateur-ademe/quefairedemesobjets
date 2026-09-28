"""Publish the open data of the fiches (produits and consignes) on S3.

The rows live in the CMS, which the Airflow Django settings do not load: the
webapp serves them as CSV on its API v1 (`/api/v1/produits.csv`,
`/api/v1/consignes.csv`), the task fetches the files and stores them next to
the acteurs export. Permanent files only, no dated snapshot: the CMS keeps
its own history.
"""

import logging

import requests
from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from utils.webapp import WEBAPP_URL

logger = logging.getLogger(__name__)

FICHES_OPENDATA_FILENAMES = ("produits.csv", "consignes.csv")
TIMEOUT_SECONDS = 120


def export_opendata_fiches_to_s3(export_opendata_config: ExportOpendataConfig):
    s3_hook = S3Hook(aws_conn_id=export_opendata_config.s3_connection_id)
    for filename in FICHES_OPENDATA_FILENAMES:
        url = f"{WEBAPP_URL}/api/v1/{filename}"
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        key = f"{export_opendata_config.fiches_remote_dir}/{filename}"
        logger.info(f"{url} → s3://{export_opendata_config.bucket_name}/{key}")
        s3_hook.load_bytes(
            response.content,
            key=key,
            bucket_name=export_opendata_config.bucket_name,
            replace=True,
            acl_policy="public-read",
        )
