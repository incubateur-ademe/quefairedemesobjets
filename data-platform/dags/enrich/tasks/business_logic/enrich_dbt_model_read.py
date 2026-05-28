"""Read data from DBT models"""

import logging

from utils.dataframes import df_filter
from utils.django import DJANGO_WH_CONNECTION_NAME

logger = logging.getLogger(__name__)


def enrich_dbt_model_read(dbt_model_name: str, filters: list[dict] = []):
    """Reads necessary QFDMO acteurs and AE entries from DB"""
    import numpy as np
    import pandas as pd

    from utils.django import django_setup_full

    django_setup_full()
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
