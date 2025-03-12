"""Read data from DB needed for RGPD anonymization"""

import numpy as np
import pandas as pd
from rgpd.config import DIR_SQL_READ
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()


def rgpd_anonymize_people_read(filter_comments_contain: str = "") -> pd.DataFrame:
    """Reads necessary QFDMO acteurs and AE entries from DB"""
    from django.db import connection

    # Get SQL query and set filter
    sql = (DIR_SQL_READ / "rgpd_anonymize_people_read.sql").read_text()
    sql = sql.replace("{{filter_comments_contain}}", filter_comments_contain)

    # Execute SQL query and get data
    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    # Create DataFrame and preview
    df = pd.DataFrame(data, columns=columns, dtype="object").replace({np.nan: None})
    log.preview_df_as_markdown("Acteurs & entrées Annuaire Entreprise", df)

    return df
