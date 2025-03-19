"""Utilities to help us integrate Airflow <-> DBT, e.g. to detect
schema issues during tests/config checks without wasting time on DAG runs"""

import json
from functools import cache
from pathlib import Path

DIR_CURRENT = Path(__file__).resolve()
DIR_DBT = DIR_CURRENT.parent.parent.parent / "dbt"


@cache
def dbt_manifest_read() -> dict:
    """Get the dbt manifest data"""
    return json.loads((DIR_DBT / "target" / "manifest.json").read_text())


def dbt_assert_model_schema(model_name: str, columns: list[str]) -> None:
    """Check if a model exists in a dbt schema with some columns"""

    # Get manifest
    manifest = dbt_manifest_read()

    # Ensure model is present
    model_key = f"model.qfdmo.{model_name}"
    if model_key not in manifest["nodes"]:
        raise ValueError(f"Model {model_name} not found in dbt manifest")

    # Ensure columns are present
    model_columns = manifest["nodes"][model_key]["columns"]
    diff = set(columns) - set(model_columns)
    if diff:
        raise ValueError(f"Columns {diff} not found in model {model_name}")
