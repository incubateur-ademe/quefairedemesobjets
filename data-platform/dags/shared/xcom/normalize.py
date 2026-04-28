"""Helpers to normalize values pulled from XCom.

Airflow 3's built-in pandas serializer round-trips DataFrames through parquet,
which converts Python list cells into numpy.ndarray. Downstream code often
relies on `isinstance(cell, list)`, so we restore lists at the pull boundary.
"""

from typing import Any

import numpy as np
import pandas as pd


def _array_to_list(cell: Any) -> Any:
    if isinstance(cell, np.ndarray):
        return [_array_to_list(v) for v in cell.tolist()]
    return cell


def normalize_xcom_value(value: Any) -> Any:
    """Restore Python list cells in DataFrames coming back from XCom."""
    if isinstance(value, pd.DataFrame):
        for col in value.select_dtypes(include="object").columns:
            if value[col].map(lambda v: isinstance(v, np.ndarray)).any():
                value[col] = value[col].map(_array_to_list)
    return value
