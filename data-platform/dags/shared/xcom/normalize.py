"""Helpers to normalize values pulled from XCom.

Airflow 3's built-in pandas serializer round-trips DataFrames through parquet,
which converts Python list cells into numpy.ndarray. Downstream code often
relies on `isinstance(cell, list)`, so we restore lists at the pull boundary.

The conversion is recursive: parquet also rewrites lists nested inside dicts
(e.g. ``[{"action": "x", "sous_categories": np.array([...])}]``) into ndarrays,
and these inner arrays must be restored too — otherwise ``json.dumps(..., default=str)``
serializes them with ``str(np.ndarray)`` (``"['petits_appareils_extincteurs']"``)
instead of as proper JSON arrays.

Parquet also turns Python ``None`` cells of object columns into ``float('nan')``
on the way back. We restore those to ``None`` so downstream code can rely on a
single, JSON-friendly null sentinel.
"""

from typing import Any

import numpy as np
import pandas as pd


def _array_to_list(cell: Any) -> Any:
    """Recursively convert numpy arrays into Python lists (including arrays
    nested inside lists/dicts) and parquet's ``nan`` null cells back to ``None``."""
    if isinstance(cell, np.ndarray):
        return [_array_to_list(v) for v in cell.tolist()]
    if isinstance(cell, list):
        return [_array_to_list(v) for v in cell]
    if isinstance(cell, dict):
        return {k: _array_to_list(v) for k, v in cell.items()}
    if isinstance(cell, float) and pd.isna(cell):
        return None
    return cell


def normalize_xcom_value(value: Any) -> Any:
    """Restore Python list cells in DataFrames coming back from XCom."""
    if isinstance(value, pd.DataFrame):
        for col in value.select_dtypes(include="object").columns:
            value[col] = value[col].map(_array_to_list)
    return value
