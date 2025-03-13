"""Read data from DB needed for enrich anonymization"""

import numpy as np
import pandas as pd
from enrich.config import (
    AE_ETAB_STATUS_MAPPING_EXPLICIT,
    AE_UNITE_STATUS_MAPPING_EXPLICIT,
    COLS,
    DIR_SQL_READ,
)
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()


def close_acteurs_via_ae_read() -> pd.DataFrame:
    """Reads necessary QFDMO acteurs and AE entries from DB"""
    from django.db import connection

    # Get SQL query and set filter
    sql = (DIR_SQL_READ / "close_acteurs_via_ae.sql").read_text()

    # Execute SQL query and get data
    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    # Create DataFrame and preview
    df = pd.DataFrame(data, columns=columns, dtype="object").replace({np.nan: None})

    # Making statuses more explicit
    df[COLS.AE_UNITE_STATUS] = df[COLS.AE_UNITE_STATUS].map(
        AE_UNITE_STATUS_MAPPING_EXPLICIT
    )
    df[COLS.AE_ETAB_STATUS] = df[COLS.AE_ETAB_STATUS].map(
        AE_ETAB_STATUS_MAPPING_EXPLICIT
    )

    # Preview
    log.preview_df_as_markdown("Acteurs & entrées Annuaire Entreprise", df)

    return df
