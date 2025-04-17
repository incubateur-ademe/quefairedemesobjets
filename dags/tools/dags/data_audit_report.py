import json
import logging
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import requests
from airflow import DAG
from airflow.decorators import task
from airflow.models import Param
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.dates import days_ago
from slugify import slugify
from utils import logging_utils as log
from utils.dicts import dicts_get_nested_key
from ydata_profiling import ProfileReport

logger = logging.getLogger("airflow.task")

default_args = {
    "owner": "airflow",
}

DATA_FORMATS = [
    "csv",
    "json",
    "excel",
    "parquet",
    "orc",
    "stata",
    "sas",
    "feather",
    "pickle",
]

with DAG(
    dag_id="data_audit_report",
    dag_display_name="📊 Audit de données depuis une URL",
    default_args=default_args,
    start_date=days_ago(1),
    schedule=None,
    params={
        # For the data we want to audit
        "data_endpoint": Param(
            (
                "https://data.ademe.fr/data-fair/api/v1/datasets/"
                "sinoe-(r)-annuaire-des-decheteries-dma/lines?size=100&q_mode=simple&ANNEE_eq=2025"
            ),
            type="string",
        ),
        "data_format": Param("json", enum=DATA_FORMATS, type="string"),
        # TODO: améliorer avec
        "data_json_nested_key": Param(
            "results",
            type=["null", "string"],
            description="""Si JSON et que la donnée est nestée, fournir le path""",
        ),
        "data_separator": Param("", type=["null", "string"]),
        "data_sampling": Param(
            1,
            type=["number"],
            minimum=0.1,
            maximum=1,
            step=0.1,
            description=r"""Fraction de sampling (0=0%, 1=100%)
            🔴 Attention: ceci s'applique à la donnée APRES téléchargement,
            donc réduire la taille du fichier via URL si possible""",
        ),
        # For the report we want to save
        "report_s3_connection_id": Param("s3data", type="string"),
        "report_s3_bucket": Param("lvao-opendata", type="string"),
        "report_s3_folder": Param("data_audit_reports", type="string"),
    },
    catchup=False,
    tags=["data", "audit", "report", "profiling", "s3"],
) as dag:

    @task()
    def data_audit_report(**context):
        now = datetime.now().strftime("%Y%m%d%H%M%S")

        # ---------------------------------------------
        # Params
        logger.info(log.banner_string("📖 Paramètres"))
        params = context["params"]
        log.preview("Paramètres", params)
        data_endpoint = params["data_endpoint"]
        data_format = params["data_format"]
        data_json_nested_key = params["data_json_nested_key"]

        # ---------------------------------------------
        # Download the data
        logger.info(log.banner_string("📥 Téléchargement"))
        logger.info(f"URL: {data_endpoint}")
        logger.info("Téléchargement: commencé 🟡")
        response = requests.get(data_endpoint)
        response.raise_for_status()
        data_bytes = BytesIO(response.content)
        data_text = StringIO(response.text)
        logger.info("Téléchargement: terminé 🟢")

        # ---------------------------------------------
        # Read the data
        logger.info(log.banner_string("📦 Création du DataFrame"))
        logger.info("Création du DataFrame: commencé 🟡")
        if data_format == "csv":
            df = pd.read_csv(data_text, sep=params.get("data_separator", ","))
        elif data_format == "json":
            data = json.loads(data_bytes.read())
            data = (
                dicts_get_nested_key(data, data_json_nested_key)
                if data_json_nested_key
                else data
            )
            df = pd.DataFrame(data)
        elif data_format == "excel":
            df = pd.read_excel(data_bytes)
        elif data_format == "parquet":
            df = pd.read_parquet(data_bytes)
        elif data_format == "orc":
            df = pd.read_orc(data_bytes)
        elif data_format == "stata":
            df = pd.read_stata(data_bytes)
        elif data_format == "sas":
            df = pd.read_sas(data_bytes)
        elif data_format == "feather":
            df = pd.read_feather(data_bytes)
        elif data_format == "pickle":
            df = pd.read_pickle(data_bytes)
        else:
            raise ValueError(f"Format non supporté: {data_format}")
        logger.info("Création du DataFrame: terminé 🟢")
        log.preview_df_as_markdown("Données téléchargées", df)

        # ---------------------------------------------
        # Filter data before running report
        data_sampling = params["data_sampling"]
        if data_sampling:
            logger.info(f"Sampling à {data_sampling}")
            logger.info(f"Nombre de lignes avant sampling: {len(df)}")
            df = df.sample(frac=data_sampling)
            logger.info(f"Nombre de lignes après sampling: {len(df)}")

        # ---------------------------------------------
        # Profile the data
        logger.info(log.banner_string("📊 Audit"))
        logger.info("Profiling: commencé 🟡")
        dataset = {
            "description": f"Audit effectué le {now} via DAG airflow {dag.dag_id}",
            "url": data_endpoint,
        }
        profile = ProfileReport(df, title="📊 Audit", minimal=True, dataset=dataset)
        report_html = profile.to_html()
        logger.info("Profiling: terminé 🟢")

        # ---------------------------------------------
        # Upload the report on S3
        logger.info(log.banner_string("📤 Upload du rapport sur S3"))
        logger.info("Upload du rapport sur S3: commencé 🟡")

        filename = (
            f"{now}_{slugify(data_endpoint.split('//')[-1].replace('/', '_'))}.html"
        )
        key = str(Path(params["report_s3_folder"], filename))
        url = f"https://s3.fr-par.scw.cloud/{params['report_s3_bucket']}/{params['report_s3_folder']}/{filename}"
        logger.info(f"{filename=}")
        logger.info(f"{key=}")
        logger.info(f"{url=}")
        S3Hook(aws_conn_id=params["report_s3_connection_id"]).load_string(
            string_data=report_html,
            key=key,
            bucket_name=params["report_s3_bucket"],
            acl_policy="public-read",
        )
        logger.info("Upload du rapport sur S3: terminé 🟢")
        logger.info(f"URL du rapport: {url}")

        # ---------------------------------------------
        # List all the reports on S3 in ascending order
        logger.info(log.banner_string("📂 Liste des rapports sur S3"))
        reports = S3Hook(aws_conn_id=params["report_s3_connection_id"]).list_keys(
            bucket_name=params["report_s3_bucket"],
            prefix=params["report_s3_folder"],
        )
        reports = sorted(reports)
        log.preview("Liste des rapports précédents", reports)

        # ---------------------------------------------
        # Display the report for this DAG
        logger.info(log.banner_string("🟢 Rapport pour ce DAG"))
        logger.info(f"Rapport pour ce DAG: {url}")

    data_audit_report()
