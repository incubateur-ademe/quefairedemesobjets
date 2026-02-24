import numpy as np
import pandas as pd


def normalize_to_list(x):
    """Return a list for scalar, list or numpy array values.

    - list -> unchanged
    - numpy.ndarray -> converted with .tolist()
    - NaN/None -> empty list
    - scalar -> wrapped in a one-element list
    """
    if isinstance(x, list):
        return x
    if isinstance(x, np.ndarray):
        return x.tolist()
    if pd.isna(x):
        return []
    return [x]


def is_empty_sequence(x) -> bool:
    """Return True if x is an empty list/array/tuple/set or NaN/None."""
    if isinstance(x, (list, tuple, set, np.ndarray)):
        return len(x) == 0
    if pd.isna(x):
        return True
    return False


def df_convert_numpy_to_jsonify(df: pd.DataFrame) -> pd.DataFrame:
    # apply convert_numpy_to_jsonify to each column of the dataframe
    for col in df.columns:
        df[col] = df[col].apply(convert_numpy_to_jsonify)
    return df


def convert_numpy_to_jsonify(obj) -> list | dict | str | int | float | bool | None:
    """Recursively convert numpy types and sequences to JSON-serialisable structures."""
    if isinstance(obj, np.ndarray):
        return [convert_numpy_to_jsonify(v) for v in obj.tolist()]
    if isinstance(obj, (list, tuple, set)):
        return [convert_numpy_to_jsonify(v) for v in obj]
    if isinstance(obj, dict):
        return {k: convert_numpy_to_jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return obj.isoformat()
    return obj
