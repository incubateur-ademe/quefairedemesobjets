"""Read data from DBT models"""

import logging

import numpy as np
import pandas as pd
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def enrich_dbt_model_read(
    dbt_model_name: str, filters: list[dict] = []
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
    filter_applied = False
    if not df.empty:
        for filter in filters:

            # Assignment & info
            filter_applied = True
            field = filter["field"]
            operator = filter["operator"]
            value = filter["value"]
            logger.info(f"\n🔽 Filtre sur {field=} {operator=} {value=}")
            logger.info(f"Avant filtre : {df.shape[0]} lignes")

            # Filtering
            if filter["operator"] == "equals":
                logger.info(f"Filtre sur {field} EQUALS {value}")
                df = df[df[field] == value].copy()
            elif filter["operator"] == "contains":
                df = df[df[field].str.contains(value, regex=True, case=False)].copy()
            else:
                raise NotImplementedError(f"{filter['operator']=} non implémenté")

            logger.info(f"Après filtre : {df.shape[0]} lignes")

    if filter_applied:
        log.preview_df_as_markdown(f"Données de {dbt_model_name} APRES filtre(s)", df)

    return df
