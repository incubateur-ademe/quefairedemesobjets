import subprocess
from io import StringIO
from unittest.mock import patch

import pytest
from acteurs.tasks.business_logic.export_opendata_csv_to_s3 import run_psql_copy

PASSWORD = "s3cret-p@ss"  # pragma: allowlist secret
DSN = f"postgres://warehouse:{PASSWORD}@db.example:5432/warehouse?sslmode=require"


def test_run_psql_copy_does_not_put_the_dsn_in_argv():
    with patch(
        "acteurs.tasks.business_logic.export_opendata_csv_to_s3.subprocess.run"
    ) as mock_run:
        run_psql_copy(DSN, "public.opendata", StringIO())

    command = mock_run.call_args.args[0]
    assert command == ["psql", "-c", "COPY public.opendata TO STDOUT WITH CSV HEADER"]
    assert PASSWORD not in " ".join(command)
    assert mock_run.call_args.kwargs["env"]["PGPASSWORD"] == PASSWORD
    assert mock_run.call_args.kwargs["env"]["PGSSLMODE"] == "require"


def test_run_psql_copy_hides_the_command_when_psql_fails():
    failure = subprocess.CalledProcessError(
        2,
        ["psql", "-d", DSN, "-c", "COPY public.opendata TO STDOUT WITH CSV HEADER"],
    )
    with patch(
        "acteurs.tasks.business_logic.export_opendata_csv_to_s3.subprocess.run",
        side_effect=failure,
    ):
        with pytest.raises(RuntimeError, match="exit code 2") as exc_info:
            run_psql_copy(DSN, "public.opendata", StringIO())

    assert PASSWORD not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True
