from typing import Union

import pandas as pd


def mapping_try_or_fallback_column_value(
    df_column: pd.Series,
    values_mapping: dict,
    default_value: Union[str, bool, None] = None,
) -> pd.Series:
    # set to default value if column is not one of keys or values in values_mapping
    return (
        df_column.str.strip()
        .str.lower()
        .replace(values_mapping)
        .apply(lambda x: (default_value if x not in values_mapping.values() else x))
    )


def cast_eo_boolean_or_string_to_boolean(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() == "oui"
    return False
