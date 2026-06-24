"""(De)serialize the parent_data_new dict column for XCom transport.

Airflow 3 serializes DataFrames to Parquet for XCom. pyarrow infers a
`struct` type for an object column of dicts, which fails when the only
non-null values are empty dicts (`Cannot write struct type with no child
field`) and silently rewrites `{}` into `{field: None, ...}` when other
rows are non-empty. To keep the dict semantics intact (including the
`{}` "keep parent, no change" case), we store the column as JSON strings
on the wire and parse it back to dicts on the other side.
"""

import json

import pandas as pd
from cluster.config.constants import COL_PARENT_DATA_NEW
from utils.data_serialize_reconstruct import parent_data_dict_to_json_ready


def parent_data_new_serialize(df: pd.DataFrame) -> pd.DataFrame:
    """dict/None -> JSON string/None, so the column survives Parquet XCom."""
    if COL_PARENT_DATA_NEW not in df.columns:
        return df
    df = df.copy()
    df[COL_PARENT_DATA_NEW] = df[COL_PARENT_DATA_NEW].map(
        lambda v: (
            None
            if v is None
            else json.dumps(parent_data_dict_to_json_ready(v), default=str)
        )
    )
    return df


def parent_data_new_deserialize(df: pd.DataFrame) -> pd.DataFrame:
    """JSON string/None -> dict/None, reversing parent_data_new_serialize.

    Parquet's ``nan`` nulls are already restored to ``None`` upstream by
    ``normalize_xcom_value`` at the XCom pull boundary.
    """
    if COL_PARENT_DATA_NEW not in df.columns:
        return df
    df = df.copy()
    df[COL_PARENT_DATA_NEW] = df[COL_PARENT_DATA_NEW].map(
        lambda v: None if v is None else json.loads(v)
    )
    return df
