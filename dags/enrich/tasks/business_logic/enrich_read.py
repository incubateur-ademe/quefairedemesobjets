"""Read data from DB needed for RGPD anonymization"""

import logging

import numpy as np
import pandas as pd
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def enrich_read(
    dbt_model_name: str, filters_contain: list[tuple[str, str]] = []
) -> pd.DataFrame:
    """Reads necessary QFDMO acteurs and AE entries from DB"""
    from django.db import connection

    # Execute SQL query and get data
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {dbt_model_name}")
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    # Create DataFrame and preview
    df = pd.DataFrame(data, columns=columns, dtype="object").replace({np.nan: None})
    log.preview_df_as_markdown(f"Données de {dbt_model_name} SANS filtre", df)

    # Filtering if needed
    if not df.empty:
        for col_name, col_value in filters_contain:
            col_value = (col_value or "").strip()
            if filter:
                logger.info(f"Filtre sur {col_name} CONTIENT {col_value}")
                df = df[df[col_name].notnull()].copy()
                df = df[
                    df[col_name].str.contains(col_value, regex=True, case=False)
                ].copy()
                log.preview_df_as_markdown(
                    f"Données de {dbt_model_name} APRES filtre", df
                )

    return df
