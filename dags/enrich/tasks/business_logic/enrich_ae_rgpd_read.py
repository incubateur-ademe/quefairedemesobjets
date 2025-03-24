"""Read data from DB needed for RGPD anonymization"""

import logging

import numpy as np
import pandas as pd
from enrich.config import COLS
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def enrich_ae_rgpd_read(
    dbt_model_name: str, filter_comments_contain: str = ""
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
    log.preview_df_as_markdown("Matches acteurs vs. Annuaire Entreprises", df)

    # Filtering if needed
    filter = (filter_comments_contain or "").strip()
    if not df.empty and filter:
        logger.info(f"Filtre sur les commentaires: {filter}")
        df = df[df[COLS.ACTEUR_COMMENTAIRES].notnull()].copy()
        df = df[
            df[COLS.ACTEUR_COMMENTAIRES].str.contains(
                filter,
                regex=True,
                case=False,
            )
        ].copy()
        log.preview_df_as_markdown("Matches APRES filtre commentaires", df)

    return df
