"""Constants and utilities for schemas"""

import re
from re import Pattern

# oyaml = wrapper around pyyaml to preserve dict order
import oyaml as yaml
import pydash

from scripts.dbt.conf.columns import db_column_to_dbt_column

# Models we don't want tests on, for instance
# base models for large datasets (e.g. BAN, AE)
# for which we will have the same tests on int_
MODELS_TO_SKIP_TESTS: list[Pattern[str]] = [
    re.compile(r"base_ban"),
    re.compile(r"base_ae"),
]


def schemas_new_generate(model: dict, db_columns: list[dict]) -> dict:
    """Create a new schema from a model"""
    dbt_columns = [db_column_to_dbt_column(model["name"], x) for x in db_columns]
    schema_new = {
        "version": 2,
        "models": [{"name": model["name"], "description": "", "columns": dbt_columns}],
    }
    return schema_new


def deep_merge_by_name(target, source) -> dict:
    """Merge two dictionaries, leveraging the "name" key" when
    present in dicts to determine identity"""
    if isinstance(target, dict) and isinstance(source, dict):
        for key, value in source.items():
            if key in target:
                target[key] = deep_merge_by_name(target[key], value)
            else:
                target[key] = value
        return target

    elif isinstance(target, list) and isinstance(source, list):
        # Merge lists of dicts with "name" keys
        if all(isinstance(x, dict) and "name" in x for x in target + source):
            merged = {d["name"]: d.copy() for d in target}
            for item in source:
                name = item["name"]
                if name in merged:
                    merged[name] = deep_merge_by_name(merged[name], item)
                else:
                    merged[name] = item.copy()
            return list(merged.values())  # type: ignore
        else:
            # If not dicts with "name", replace the list
            return source  # type: ignore

    else:
        # Scalar or incompatible types: source overwrites target
        return source


def schemas_merge(old: dict, new: dict) -> dict:
    """Merge two dictionaries of schemas"""
    merged = deep_merge_by_name(old.copy(), new.copy())
    return merged


def schemas_contract_enforce(schema: dict) -> dict:
    """Enforce DBT contract on a schema"""
    for model in schema["models"]:
        pydash.objects.set_(model, "config.contract.enforced", True)
    return schema


def schemas_remove_unwanted_data_tests(schema: dict) -> dict:
    """Remove unwanted data tests from a schema"""
    for model in schema["models"]:
        if any(pattern.search(model["name"]) for pattern in MODELS_TO_SKIP_TESTS):
            for column in model["columns"]:
                if "data_tests" in column:
                    del column["data_tests"]
    return schema


class IndentListDumper(yaml.SafeDumper):
    """Ensures extra indentation for lists
    https://medium.com/@reorx/tips-that-may-save-you-from-the-hell-of-pyyaml-572cde7e1d6f
    """

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, indentless=False)


def schema_to_yaml(schema: dict) -> str:
    """Convert a schema to a YAML string"""
    return yaml.dump(
        schema,
        sort_keys=False,
        default_flow_style=False,
        Dumper=IndentListDumper,
        allow_unicode=True,
    )
