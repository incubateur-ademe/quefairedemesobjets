from scripts.dbt.conf.schemas import schema_to_yaml, schemas_merge

SCHEMA_OLD = {
    "version": 2,
    "models": [
        # Not present in new, will be kept as-is
        {"name": "foo1"},
        # Present in new with columns, columns be added
        {"name": "foo2"},
        {"name": "foo4", "columns": [{"name": "test1"}]},
    ],
}
SCHEMA_NEW = {
    "models": [
        {"name": "foo2", "columns": [{"name": "test", "data_type": "integer"}]},
        # Not present in old, will be added
        {"name": "foo3"},
        {"name": "foo4", "columns": [{"name": "test2"}]},
    ],
}

SCHEMA_MERGED = {
    "models": [
        {"name": "foo1"},
        {"name": "foo2", "columns": [{"name": "test", "data_type": "integer"}]},
        {"name": "foo4", "columns": [{"name": "test1"}, {"name": "test2"}]},
        {"name": "foo3"},
    ],
    "version": 2,
}


def test_schemas_merge():
    assert schemas_merge(SCHEMA_OLD, SCHEMA_NEW) == SCHEMA_MERGED


def test_schema_to_yaml():
    yaml = schema_to_yaml(SCHEMA_OLD)
    expected = """version: 2
models:
  - name: foo1
  - name: foo2
  - name: foo4
    columns:
      - name: test1
"""
    assert yaml == expected
