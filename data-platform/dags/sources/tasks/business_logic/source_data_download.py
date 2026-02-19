import logging
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from shared.config.airflow import TMP_FOLDER
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_download(
    endpoint: str,
    s3_connection_id: str | None = None,
    metadata_endpoint: str | None = None,
) -> pd.DataFrame:
    """Téléchargement de la données source sans lui apporter de modification"""

    def _align_columns_with_schema(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
        # Récupérer toutes les colonnes attendues du schéma
        expected_columns = [
            field["key"] for field in schema if not field.get("x-calculated", False)
        ]

        # Vérifier les colonnes manquantes
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            logger.warning(f"Colonnes manquantes dans le DataFrame : {missing_columns}")
        for column in missing_columns:
            df[column] = ""

        # Vérifier les colonnes supplémentaires non attendues
        extra_columns = set(df.columns) - set(expected_columns)
        if extra_columns:
            logger.warning(
                f"Colonnes supplémentaires dans le DataFrame : {extra_columns}"
            )

        log.preview("metadata retournée par la tâche", schema)
        return df

    logger.info("Téléchargement données de l'API : début...")
    # TODO: changer de logique, plutôt que de tout charger en mémoire et se
    # trimballer des dataframes en XCOM, on devrait plutôt streamer les données
    # directement dans la base de données et déléguer le traitement à la DB
    # tant que possible
    data = fetch_data_from_endpoint(endpoint, s3_connection_id)
    logger.info("Téléchargement données de l'API : ✅ succès.")
    df = pd.DataFrame(data).replace({pd.NA: None, np.nan: None})
    # create dataframe with only string, boolean or list dtype columns
    for column in df.columns:
        if df[column].dtype not in [str, bool, list]:
            df[column] = df[column].astype(str)
    if df.empty:
        raise ValueError("Aucune donnée reçue de l'API")
    log.preview("df retournée par la tâche", df)

    if metadata_endpoint:
        metadata = requests.get(metadata_endpoint, timeout=60)
        metadata.raise_for_status()
        schema = metadata.json()
        df = _align_columns_with_schema(df, schema)

    return df


def fetch_data_from_endpoint(endpoint, s3_connection_id):
    if endpoint.startswith("s3://"):
        return fetch_dataset_from_s3(endpoint, s3_connection_id)
    elif "pointsapport.ademe.fr" in endpoint or "data.ademe.fr" in endpoint:
        return fetch_dataset_from_point_apport(endpoint)
    elif "apiopendata.artisanat.fr" in endpoint:
        return fetch_dataset_from_artisanat(endpoint)
    elif "ordre.pharmacien.fr" in endpoint:
        return fetch_dataset_from_pharmacies(endpoint)
    # Le but de nos intégrations API est de récupérer des données.
    # Si on ne récupére pas de données, on sait qu'on à un problème,
    # et donc il faut échouer explicitement au plus tôt
    raise NotImplementedError(f"Pas de fonction de récupération pour l'url {endpoint}")


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
