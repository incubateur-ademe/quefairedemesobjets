import logging
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_download(endpoint: str) -> pd.DataFrame:
    """Téléchargement de la données source sans lui apporter de modification"""
    logger.info("Téléchargement données de l'API : début...")
    # TODO: changer de logique, plutôt que de tout charger en mémoire et se
    # trimballer des dataframes en XCOM, on devrait plutôt streamer les données
    # directement dans la base de données et déléguer le traitement à la DB
    # tant que possible
    data = fetch_data_from_endpoint(endpoint)
    logger.info("Téléchargement données de l'API : ✅ succès.")
    df = pd.DataFrame(data).replace({pd.NA: None, np.nan: None})
    if df.empty:
        raise ValueError("Aucune donnée reçue de l'API")
    log.preview("df retournée par la tâche", df)
    return df


def fetch_data_from_endpoint(endpoint):
    if "pointsapport.ademe.fr" in endpoint or "data.ademe.fr" in endpoint:
        return fetch_dataset_from_point_apport(endpoint)
    elif "artisanat.fr" in endpoint:
        return fetch_dataset_from_artisanat(endpoint)
    elif "ordre.pharmacien.fr" in endpoint:
        return fetch_dataset_from_pharmacies(endpoint)
    # Le but de nos intégrations API est de récupérer des données.
    # Si on ne récupére pas de données, on sait qu'on à un problème,
    # et donc il faut échouer explicitement au plus tôt
    raise NotImplementedError(f"Pas de fonction de récupération pour l'url {endpoint}")


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
    offset = 0
    total_records = requests.get(base_url, params={"limit": 1, "offset": 0}).json()[
        "total_count"
    ]
    records_per_request = 100
    params = {"limit": records_per_request, "offset": 0}
    while offset < total_records:
        params.update({"offset": offset})
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data["results"])
            offset += records_per_request
        else:
            response.raise_for_status()

    return all_data


def fetch_dataset_from_pharmacies(endpoint):
    with tempfile.TemporaryDirectory() as temp_dir:
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
