import logging

import numpy as np
import pandas as pd
from utils import api_utils
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_download_wrapper(**kwargs) -> pd.DataFrame:
    params = kwargs["params"]
    api_url = params["endpoint"]

    log.preview("API end point", api_url)

    return source_data_download(api_url=api_url)


def source_data_download(api_url: str) -> pd.DataFrame:
    """Téléchargement de la données source sans lui apporter de modification"""
    logger.info("Téléchargement données de l'API : début...")
    # TODO: changer de logique, plutôt que de tout charger en mémoire et se
    # trimballer des dataframes en XCOM, on devrait plutôt streamer les données
    # directement dans la base de données et déléguer le traitement à la DB
    # tant que possible
    data = api_utils.fetch_data_from_url(api_url)
    logger.info("Téléchargement données de l'API : ✅ succès.")
    df = pd.DataFrame(data).replace({pd.NA: None, np.nan: None})
    if df.empty:
        raise ValueError("Aucune donnée reçue de l'API")
    log.preview("df retournée par la tâche", df)
    return df
