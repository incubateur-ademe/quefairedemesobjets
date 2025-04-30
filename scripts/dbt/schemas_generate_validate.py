"""Script to help generate and validate dbt schemas"""

import json
import re
import sys
from pathlib import Path

import yaml
from rich import print
from rich.prompt import Prompt
from rich.traceback import install
from sqlalchemy import inspect

install()

# Paths
DIR_ROOT = Path(__file__).parent.parent.parent
DIR_DBT = DIR_ROOT / "dbt"
DIR_DBT_MODELS = DIR_DBT / "models"
DIR_DAGS = DIR_ROOT / "dags"
FP_DBT_MANIFEST = DIR_DBT / "target" / "manifest.json"
sys.path.append(str(DIR_ROOT))
sys.path.append(str(DIR_DAGS))

# Django setup
from utils.django import (  # noqa: E402
    django_conn_to_sqlalchemy_engine,
    django_setup_full,
)

from scripts.dbt.conf.schemas import (  # noqa: E402
    schema_to_yaml,
    schemas_merge,
    schemas_new_generate,
    schemas_remove_unwanted_data_tests,
)

django_setup_full()


def dbt_manifest_to_models() -> list[dict]:
    """Return a list of models from the manifest file"""
    with open(FP_DBT_MANIFEST, "r") as f:
        manifest = json.load(f)

    return [
        node
        for node in manifest.get("nodes", {}).values()
        if node["resource_type"] == "model"
    ]


def dbt_model_schema_process(engine, model: dict):
    """Generate, validate and update a dbt model schema"""

    # Get DB columns
    inspector = inspect(engine)
    try:
        db_columns = inspector.get_columns(model["name"])  # type: ignore
    except Exception as e:
        print(f"Error getting columns for model {model['name']}: {e}")
        return

    # Generate new schema
    schema_new = schemas_new_generate(model, db_columns)

    # Validate
    path_schemas = (
        DIR_DBT_MODELS / "/".join(model["path"].split("/")[:-1]) / "schema.yml"
    )
    # TODO: below could be replaced with automation to create schema w/ template
    assert path_schemas.exists(), f"Schema manquant: {path_schemas}"
    if path_schemas.exists():
        assert "models" in path_schemas.read_text(), "Need to create schema template"

    # Generate new schema
    schema_old = yaml.safe_load(path_schemas.read_text())
    schema_new = schemas_merge(schema_old, schema_new)
    schema_new = schemas_remove_unwanted_data_tests(schema_new)
    # schema_new = schemas_contract_enforce(schema_new)

    # Update schema file: thanks to merge, will only update current
    # model and leave other models unchanged
    path_schemas.write_text(schema_to_yaml(schema_new))


if __name__ == "__main__":
    # Ensuring DB connection OK before doing anything else
    engine = django_conn_to_sqlalchemy_engine()

    # Getting (and optionally filtering) DBT models
    ask = "dbt model name pattern (none=*)"
    model_pattern = Prompt.ask(ask, default="base_ban")
    models = dbt_manifest_to_models()
    if model_pattern:
        models = [x for x in models if re.search(model_pattern, x["name"])]

    # Processing each model
    for model in models:
        dbt_model_schema_process(engine, model)
