"""Read data from DBT models"""

import logging

import numpy as np
import pandas as pd

from utils.dataframes import df_filter
from utils.django import DJANGO_WH_CONNECTION_NAME, django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def enrich_dbt_model_read(
    dbt_model_name: str, filters: list[dict] = []
) -> pd.DataFrame:
    """Reads necessary QFDMO acteurs and AE entries from DB"""
    from django.db import connections

    logger.info(f"Lecture des données de {dbt_model_name}")

    # Execute SQL query and get data
    with connections[DJANGO_WH_CONNECTION_NAME].cursor() as cursor:
        cursor.execute(f"SELECT * FROM {dbt_model_name}")
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    # Create DF from Django data
    logger.info("Création du DF")
    df = pd.DataFrame(data, columns=columns, dtype="object").replace({np.nan: None})

    # Filtering
    logger.info("Filtre sur les données")
    df = df_filter(df, filters)

    return df
