# qfdmo/xcom_payloads.py (suite)

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class DataFrameXCom:
    """
    Wrapper générique pour DataFrame en XCom.
    """

    __version__ = 1
    # list of row dicts (DataFrame.to_dict(orient="records"))
    data: list[dict[Any, Any]]

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> "DataFrameXCom":
        # Ici tu peux réutiliser df_convert_numpy_to_jsonify si tu veux
        from sources.tasks.transform.sequence_utils import df_convert_numpy_to_jsonify

        df_clean = df_convert_numpy_to_jsonify(df.copy())
        # on stocke un format simple (records) pour rester 100% JSON
        return cls(data=df_clean.to_dict(orient="records"))

    def to_df(self) -> pd.DataFrame:
        return pd.DataFrame.from_records(self.data)

    def serialize(self) -> dict[str, Any]:
        # primitives uniquement
        return {"data": self.data}

    @classmethod
    def deserialize(cls, data: dict[str, Any], version: int) -> "DataFrameXCom":
        return cls(data=data["data"])
