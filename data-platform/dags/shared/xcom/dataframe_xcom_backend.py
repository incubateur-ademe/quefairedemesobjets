"""
XCOM backend for handling DataFrame serialization with numpy type conversion.

This backend automatically converts numpy types and other non-JSON-serializable
objects to JSON-compatible formats before storing XCOMs.
"""

import importlib
from typing import Any

import pandas as pd
from airflow.sdk.bases.xcom import BaseXCom
from pydantic import BaseModel


class DataFrameXComBackend(BaseXCom):
    """
    Custom XCOM backend that handles DataFrame serialization with numpy type conversion.

    Automatically processes DataFrames and other values to convert numpy types to
    JSON-serializable formats.
    """

    @staticmethod
    def serialize_value(
        value: Any,
        *,
        key: str | None = None,
        task_id: str | None = None,
        dag_id: str | None = None,
        run_id: str | None = None,
        map_index: int | None = None,
    ) -> Any:
        """Serialize value, handling DataFrames and numpy types."""
        return DataFrameXComBackend._process_value(value)

    @staticmethod
    def deserialize_value(result: Any) -> Any:
        """Deserialize value, rebuilding DataFrames marked with __dataframe__."""
        value = getattr(result, "value", result)
        return DataFrameXComBackend._restore_value(value)

    @staticmethod
    def _process_value(value: Any) -> Any:
        """Process value to handle DataFrames and numpy types."""
        from sources.tasks.transform.sequence_utils import (
            convert_numpy_to_jsonify,
            df_convert_numpy_to_jsonify,
        )

        if isinstance(value, pd.DataFrame):
            df_clean = df_convert_numpy_to_jsonify(value.copy())
            return {
                "__dataframe__": True,
                "data": df_clean.to_dict(orient="records"),
            }
        elif isinstance(value, BaseModel):
            cls = type(value)
            computed = set(cls.model_computed_fields.keys())
            return {
                "__pydantic_model__": f"{cls.__module__}.{cls.__qualname__}",
                "data": DataFrameXComBackend._process_value(
                    value.model_dump(mode="json", exclude=computed)
                ),
            }
        elif isinstance(value, dict):
            return {k: DataFrameXComBackend._process_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [DataFrameXComBackend._process_value(v) for v in value]
        else:
            return convert_numpy_to_jsonify(value)

    @staticmethod
    def _restore_value(value: Any) -> Any:
        """Restore value, reconstructing DataFrames from their serialized form."""
        if isinstance(value, dict):
            if value.get("__dataframe__") is True:
                return pd.DataFrame(value.get("data", []))
            if "__pydantic_model__" in value:
                module_path, _, class_name = value["__pydantic_model__"].rpartition(".")
                cls = getattr(importlib.import_module(module_path), class_name)
                data = DataFrameXComBackend._restore_value(value.get("data", {}))
                return cls.model_validate(data)
            return {k: DataFrameXComBackend._restore_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [DataFrameXComBackend._restore_value(v) for v in value]
        return value
