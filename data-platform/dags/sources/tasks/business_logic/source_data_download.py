import logging
import re
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from shared.config.airflow import TMP_FOLDER
from utils import logging_utils as log
from utils.db_tmp_tables import infer_postgresql_array_dtypes
from utils.django import django_setup_full

logger = logging.getLogger(__name__)


def drop_rows_with_null_or_empty_fields(
    data: list | pd.DataFrame, fields: list[str] | None = None
) -> list | pd.DataFrame:
    """Supprime les lignes dont au moins un des champs listés est null."""
    if not fields:
        return data

    if isinstance(data, pd.DataFrame):
        logger.warning(
            "drop_rows_with_null_or_empty_fields is not applied on a DataFrame"
        )
        return data

    if isinstance(data, list) and data and isinstance(data[0], dict):
        before = len(data)

        def _has_null_or_empty_field(row: dict) -> bool:
            return any(
                row.get(field) is None or row.get(field) == "" for field in fields
            )

        null_or_empty_rows = [row for row in data if _has_null_or_empty_field(row)]
        filtered = [row for row in data if not _has_null_or_empty_field(row)]
        removed = before - len(filtered)
        if removed:
            logger.error(
                f"Lignes avec champ(s) null ({fields}) supprimées : "
                f"{removed} / {before}"
            )
            log.preview("lignes avec champ(s) null supprimées", null_or_empty_rows)
        return filtered

    return data


def _align_columns_with_schema(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    expected_columns = [
        field["key"] for field in schema if not field.get("x-calculated", False)
    ]

    missing_columns = set(expected_columns) - set(df.columns)
    if missing_columns:
        logger.warning(f"Colonnes manquantes dans le DataFrame : {missing_columns}")
    for column in missing_columns:
        df[column] = ""

    extra_columns = set(df.columns) - set(expected_columns)
    if extra_columns:
        logger.warning(f"Colonnes supplémentaires dans le DataFrame : {extra_columns}")

    log.preview("metadata retournée par la tâche", schema)
    return df


def _coerce_legacy_download_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Cast non-string/bool/list columns to str (legacy XCom path)."""
    for column in df.columns:
        if df[column].dtype not in [str, bool, list]:
            df[column] = df[column].astype(str)
    return df


def download_source_dataframe(
    endpoint: str,
    s3_connection_id: str | None = None,
    metadata_endpoint: str | None = None,
    ignore_rows_with_null_or_empty_fields: list[str] | None = None,
) -> pd.DataFrame:
    """Fetch source data and build a raw dataframe (no persistence)."""
    logger.info("Téléchargement données de l'API : début...")
    data = fetch_data_from_endpoint(endpoint, s3_connection_id)
    logger.info("Téléchargement données de l'API : ✅ succès.")
    logger.info(
        "Suppression des lignes avec champ(s) null ou vide : %s",
        ignore_rows_with_null_or_empty_fields,
    )
    data = drop_rows_with_null_or_empty_fields(
        data, ignore_rows_with_null_or_empty_fields
    )
    df = pd.DataFrame(data).replace({pd.NA: None, np.nan: None})
    if df.empty:
        raise ValueError("Aucune donnée reçue de l'API")
    log.preview("df retournée par la tâche", df)

    if metadata_endpoint:
        metadata = requests.get(metadata_endpoint, timeout=60)
        metadata.raise_for_status()
        schema = metadata.json()
        df = _align_columns_with_schema(df, schema)

    return df


def save_source_dataframe_in_warehouse_db(df: pd.DataFrame, dag_id: str) -> None:
    """Persist downloaded data in the warehouse and point `{dag_id}_in_use` at it."""
    django_setup_full()
    from django.db import connections
    from utils.django import DJANGO_WH_CONNECTION_NAME, django_conn_to_sqlalchemy_engine

    table_name = f"{dag_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    view_name = f"{dag_id}_in_use"
    logger.info("Enregistrement du dataframe en DB nommée %s", table_name)
    logger.info("Faire pointer une vue vers cette table nommée %s", view_name)

    connection = connections[DJANGO_WH_CONNECTION_NAME]
    engine = django_conn_to_sqlalchemy_engine(using=DJANGO_WH_CONNECTION_NAME)

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
        dtype=infer_postgresql_array_dtypes(df),
    )

    quoted_table_name = f'"{table_name}"'
    quoted_view_name = f'"{view_name}"'
    table_name_pattern = re.compile(rf"^{re.escape(dag_id)}_\d{{14}}$")

    with connection.cursor() as cursor:
        cursor.execute(f"DROP VIEW IF EXISTS {quoted_view_name} CASCADE")
        cursor.execute(
            f"CREATE VIEW {quoted_view_name} AS SELECT * FROM {quoted_table_name}"
        )
        tbls_all = connection.introspection.table_names()
        tbls_matched = sorted(
            (x for x in tbls_all if table_name_pattern.match(x)),
            reverse=True,
        )
        for old_table in tbls_matched[2:]:
            cursor.execute(f'DROP TABLE IF EXISTS "{old_table}"')


def source_data_download(
    endpoint: str,
    dag_id: str,
    s3_connection_id: str | None = None,
    metadata_endpoint: str | None = None,
    ignore_rows_with_null_or_empty_fields: list[str] | None = None,
    save_datasource_in_warehouse_db: bool = True,
) -> pd.DataFrame:
    """Téléchargement de la données source sans lui apporter de modification"""
    df = download_source_dataframe(
        endpoint=endpoint,
        s3_connection_id=s3_connection_id,
        metadata_endpoint=metadata_endpoint,
        ignore_rows_with_null_or_empty_fields=ignore_rows_with_null_or_empty_fields,
    )

    if save_datasource_in_warehouse_db:
        save_source_dataframe_in_warehouse_db(df, dag_id)
    else:
        df = _coerce_legacy_download_dtypes(df)

    return df


def fetch_data_from_endpoint(endpoint, s3_connection_id):
    if endpoint.startswith("s3://"):
        return fetch_dataset_from_s3(endpoint, s3_connection_id)
    elif (
        "pointsapport.ademe.fr" in endpoint
        or "data.ademe.fr" in endpoint
        or "sinoe-dechets.ademe.fr" in endpoint
    ):
        return fetch_dataset_from_point_apport(endpoint)
    elif "apiopendata.artisanat.fr" in endpoint:
        return fetch_dataset_from_artisanat(endpoint)
    elif "ordre.pharmacien.fr" in endpoint:
        return fetch_dataset_from_pharmacies(endpoint)

    # endpoint which return raw json data in one block (no iteration)
    if (
        endpoint.startswith("http")
        and not endpoint.endswith(".zip")
        and not endpoint.endswith(".csv")
        and "?" not in endpoint
    ):
        return fetch_dataset_from_endpoint(endpoint)

    # The purpose of our API integrations is to retrieve data.
    # If we don't retrieve any data, we know we have a problem,
    # and therefore we need to fail explicitly at the earliest possible time.
    raise NotImplementedError(f"Pas de fonction de récupération pour l'url {endpoint}")


def fetch_dataset_from_endpoint(endpoint):
    logger.info(f"Récupération de données pour {endpoint}")
    response = requests.get(endpoint, timeout=60)
    response.raise_for_status()
    data = response.json()
    logger.info("Nombre de lignes récupérées: " + str(len(data)))
    return data


def fetch_dataset_from_s3(endpoint, s3_connection_id):
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook

    s3_hook = S3Hook(aws_conn_id=s3_connection_id)

    bucket = endpoint.split("//")[1].split("/")[0]
    key = "/".join(endpoint.split("//")[1].split("/")[1:])

    temp_file_path = s3_hook.download_file(key=key, bucket_name=bucket)

    df = pd.read_excel(temp_file_path)
    return df


def fetch_dataset_from_point_apport(url):
    all_data = []
    while url:
        logger.info(f"Récupération de données pour {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        logger.info("Nombre de lignes récupérées: " + str(len(data["results"])))
        all_data.extend(data["results"])
        url = data.get("next", None)
    logger.info("Plus d'URL à parcourir")
    logger.info("Nombre total de lignes récupérées: " + str(len(all_data)))
    return all_data


def fetch_dataset_from_artisanat(base_url):
    all_data = []
    page = 0
    page_size = 1000
    total_entries = requests.get(base_url, params={"page": 1, "page_size": 1}).json()[
        "total_entries"
    ]
    params = {"page": page, "page_size": page_size}
    while page * page_size < total_entries:
        page = page + 1
        params.update({"page": page})
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data["data"])
        else:
            response.raise_for_status()

    return all_data


def fetch_dataset_from_pharmacies(endpoint):
    with tempfile.TemporaryDirectory(dir=TMP_FOLDER) as temp_dir:
        zip_file = _download_file(endpoint, temp_dir)
        unzip_files = _extract_zip(zip_file, temp_dir)
        etablissements_file = [f for f in unzip_files if "etablissements" in f][0]
        df_etablissements = _read_csv(Path(temp_dir) / etablissements_file)
    return df_etablissements


def _download_file(url, dest_folder="."):
    local_filename = Path(dest_folder) / url.split("/")[-1]
    with requests.get(url) as r:
        with open(local_filename, "wb") as f:
            f.write(r.content)
    return local_filename


def _extract_zip(zip_file, dest_folder="."):
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(dest_folder)
    return zip_ref.namelist()


def _read_csv(csv_file):
    df = pd.read_csv(csv_file, sep=";", encoding="utf-16-le", on_bad_lines="warn")
    return df
