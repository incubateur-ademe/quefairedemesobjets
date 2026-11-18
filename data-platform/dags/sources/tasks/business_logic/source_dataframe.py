"""
Valeurs nulles et typage chaîne pour les dataframes sources (download → entrepôt
 → normalize).
"""

import pandas as pd

REPLACE_NULL_MAPPING = {
    key: ""
    for key in ["null", "none", "nan", "na", "n/a", "non applicable", "aucun", "-"]
}


def is_null_sentinel(value) -> bool:
    if value is None or pd.isna(value):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return True
        if stripped.lower() in REPLACE_NULL_MAPPING:
            return True
    return False


def null_sentinel_to_none(value):
    if is_null_sentinel(value):
        return None
    return value


def normalize_source_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remplace NaN et chaînes sentinelles (ex. \"None\") par None avant persistance ou
    usage.
    """
    return df.map(null_sentinel_to_none)


def value_to_str_preserving_null(value):
    """Cast en str sans transformer les absences en \"None\" / \"nan\"."""
    if is_null_sentinel(value):
        return None
    return str(value)


def coerce_source_dataframe_to_str(df: pd.DataFrame) -> pd.DataFrame:
    from utils.db_tmp_tables import column_contains_lists

    for column in df.columns:
        if column_contains_lists(df[column]):
            continue
        if df[column].dtype == bool:
            continue
        df[column] = df[column].map(value_to_str_preserving_null)
    return df
