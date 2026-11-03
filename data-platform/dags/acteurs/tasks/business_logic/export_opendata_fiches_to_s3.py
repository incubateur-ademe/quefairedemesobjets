"""Publish the open data of the fiches (produits and consignes) on S3.

The rows live in the CMS, which the Airflow Django settings do not load: the
webapp serves them as CSV on its API v1 (`/api/v1/produits` and
`/api/v1/consignes` with `Accept: text/csv`), the task fetches each file and
stores it like the acteurs export: a dated copy per run, and the undated file
as the latest state.
"""

import logging

import pendulum
import requests
from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from utils.webapp import WEBAPP_URL

logger = logging.getLogger(__name__)

FICHES_OPENDATA_FILENAMES = ("produits.csv", "consignes.csv")
TIMEOUT_SECONDS = 120


def export_opendata_fiche_to_s3(
    export_opendata_config: ExportOpendataConfig, filename: str
):
    url = f"{WEBAPP_URL}/api/v1/{filename.removesuffix('.csv')}"
    response = requests.get(
        url, headers={"Accept": "text/csv"}, timeout=TIMEOUT_SECONDS
    )
    response.raise_for_status()

    remote_dir = export_opendata_config.fiches_remote_dir
    timestamp = pendulum.now("UTC").strftime("%Y%m%d%H%M%S")
    s3_hook = S3Hook(aws_conn_id=export_opendata_config.s3_connection_id)
    s3_hook.load_bytes(
        response.content,
        key=f"{remote_dir}/{timestamp}_{filename}",
        bucket_name=export_opendata_config.bucket_name,
        replace=True,
    )
    key = f"{remote_dir}/{filename}"
    logger.info("%s → s3://%s/%s", url, export_opendata_config.bucket_name, key)
    s3_hook.load_bytes(
        response.content,
        key=key,
        bucket_name=export_opendata_config.bucket_name,
        replace=True,
        acl_policy="public-read",
    )
