import os

import pytest
from shared.psql.utils import psql_env_from_dsn

PASSWORD = "s3cret-p@ss"  # pragma: allowlist secret
DSN = f"postgres://warehouse:{PASSWORD}@db.example:5432/warehouse?sslmode=require"


def test_psql_env_from_dsn_keeps_password_out_of_conninfo():
    env = psql_env_from_dsn(DSN)

    assert env["PGHOST"] == "db.example"
    assert env["PGPORT"] == "5432"
    assert env["PGUSER"] == "warehouse"
    assert env["PGDATABASE"] == "warehouse"
    assert env["PGPASSWORD"] == PASSWORD
    assert env["PGSSLMODE"] == "require"
    assert env["PATH"] == os.environ["PATH"]


def test_psql_env_from_dsn_decodes_percent_encoded_password():
    env = psql_env_from_dsn("postgres://warehouse:p%40ss@db.example/warehouse")

    assert env["PGPASSWORD"] == "p@ss"  # pragma: allowlist secret


def test_psql_env_from_dsn_rejects_unknown_parameter():
    dsn = "postgres://warehouse:x@db.example/warehouse?unknown_option=1"
    with pytest.raises(ValueError, match="unknown_option"):
        psql_env_from_dsn(dsn)
