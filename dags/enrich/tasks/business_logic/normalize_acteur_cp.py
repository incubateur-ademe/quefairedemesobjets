"""Read acteur with non conform code postal"""

import logging

import pandas as pd
from enrich.config.columns import COLS
from sources.tasks.transform.transform_column import clean_code_postal

logger = logging.getLogger(__name__)


def normalize_acteur_cp(df: pd.DataFrame) -> pd.DataFrame:
    def get_clean_code_postal(row):
        return clean_code_postal(row, None)

    df[COLS.SUGGEST_CODE_POSTAL] = df["code_postal"].apply(get_clean_code_postal)
    df[COLS.ACTEUR_ID] = df["identifiant_unique"]
    return df
