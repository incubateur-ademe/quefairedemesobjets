from unittest.mock import patch

import pytest
from clone.config.models import DIR_SQL_CREATION
from clone.tasks.business_logic.clone_table_create import (
    commands_download_to_disk_first,
    commands_stream_directly,
)
from pydantic import AnyUrl

PASSWORD = "s3cret-p@ss"  # pragma: allowlist secret
DSN = f"postgres://warehouse:{PASSWORD}@db.example:5432/warehouse?sslmode=require"


class TestSqlTablesCreation:

    @pytest.mark.parametrize("path", list((DIR_SQL_CREATION / "tables").glob("*.sql")))
    def test_sql_content(self, path):
        # Making sure the key statements are present in the SQL
        sql = path.read_text()
        sql = sql.replace(r"{{table_name}}", "my_table")
        # We DON'T drop tables during creation as they are versioned
        assert "DROP TABLE" not in sql
        assert "CREATE TABLE my_table" in sql


class TestCommands:

    def test_stream_zip(self):
        # Stream a file directly to DB
        with patch(
            "clone.tasks.business_logic.clone_table_create.cmd_run"
        ) as mock_cmd_run:
            commands_stream_directly(
                data_endpoint=AnyUrl(
                    url="https://example.com/StockUniteLegale_utf8.zip"
                ),
                delimiter=",",
                table_name="my_table",
                dry_run=True,
            )
            assert len(mock_cmd_run.call_args_list) == 1
            assert all(
                x in mock_cmd_run.call_args_list[0][0][0]
                for x in ["curl", "zcat", "psql"]
            )

    def test_stream_csv_keeps_the_dsn_out_of_the_command(self):
        with (
            patch("clone.tasks.business_logic.clone_table_create.cmd_run") as mock_cmd,
            patch("django.conf.settings.DB_WAREHOUSE", DSN),
        ):
            commands_stream_directly(
                data_endpoint=AnyUrl(url="https://example.com/stock.csv.gz"),
                delimiter=",",
                table_name="my_table",
                dry_run=False,
            )

        command = mock_cmd.call_args.args[0]
        assert "psql -c" in command
        assert "-d " not in command
        assert PASSWORD not in command
        assert "db.example" not in command
        env = mock_cmd.call_args.kwargs["env"]
        assert env["PGPASSWORD"] == PASSWORD
        assert env["PGHOST"] == "db.example"
        assert env["PGPORT"] == "5432"
        assert env["PGUSER"] == "warehouse"
        assert env["PGDATABASE"] == "warehouse"
        assert env["PGSSLMODE"] == "require"

    def test_stream_geojson_keeps_the_dsn_out_of_the_command(self):
        with (
            patch("clone.tasks.business_logic.clone_table_create.cmd_run") as mock_cmd,
            patch("django.conf.settings.DB_WAREHOUSE", DSN),
        ):
            commands_stream_directly(
                data_endpoint=AnyUrl(url="https://example.com/contours.geojson.gz"),
                delimiter=",",
                table_name="my_table",
                dry_run=False,
            )

        command = mock_cmd.call_args.args[0]
        assert 'ogr2ogr -f "PostgreSQL" "PG:"' in command
        assert PASSWORD not in command
        assert "db.example" not in command
        env = mock_cmd.call_args.kwargs["env"]
        assert env["PGPASSWORD"] == PASSWORD
        assert env["PGHOST"] == "db.example"
        assert env["PGDATABASE"] == "warehouse"
        assert env["PGSSLMODE"] == "require"

    def test_download_zip(self):
        with (
            patch(
                "clone.tasks.business_logic.clone_table_create.cmd_run"
            ) as mock_cmd_run,
            patch("clone.tasks.business_logic.clone_table_create.TMP_FOLDER", "/tmp"),
        ):
            commands_download_to_disk_first(
                # Testing a case similar to Annuaire Entreprises where
                # the URL filename doesn't match the extracted filename
                # (StockUniteLegale_utf8.zip -> StockUniteLegale_utf8.csv)
                data_endpoint=AnyUrl(
                    url="https://example.com/StockUniteLegale_utf8.zip"
                ),
                file_downloaded="StockUniteLegale_utf8.zip",
                file_unpacked="StockUniteLegale_utf8.csv",
                delimiter=",",
                convert_downloaded_file_to_utf8=False,
                fix_corrupted_utf8_sed_substitutions=[],
                table_name="my_table",
                dry_run=True,
            )
            assert len(mock_cmd_run.call_args_list) == 4
            assert "curl" in mock_cmd_run.call_args_list[0][0][0]
            assert "unzip" in mock_cmd_run.call_args_list[1][0][0]
            assert "wc" in mock_cmd_run.call_args_list[2][0][0]
            assert "psql" in mock_cmd_run.call_args_list[3][0][0]

    def test_download_gz(self):
        # mock cmd_run
        with (
            patch(
                "clone.tasks.business_logic.clone_table_create.cmd_run"
            ) as mock_cmd_run,
            patch("clone.tasks.business_logic.clone_table_create.TMP_FOLDER", "/tmp"),
        ):
            commands_download_to_disk_first(
                data_endpoint=AnyUrl(url="https://example.com/adresses-france.csv.gz"),
                file_downloaded="adresses-france.csv.gz",
                file_unpacked="adresses-france.csv",
                delimiter=";",
                convert_downloaded_file_to_utf8=False,
                fix_corrupted_utf8_sed_substitutions=[],
                table_name="my_table",
                dry_run=True,
            )
            assert len(mock_cmd_run.call_args_list) == 4
            assert "curl" in mock_cmd_run.call_args_list[0][0][0]
            assert "zcat" in mock_cmd_run.call_args_list[1][0][0]
            assert "wc" in mock_cmd_run.call_args_list[2][0][0]
            assert "psql" in mock_cmd_run.call_args_list[3][0][0]

    def test_download_gz_with_fix_corrupted_utf8(self):
        substitutions = [
            r"s/entr\xef\xbf\xbd\xa9e/entrée/",
            r"s/foo/bar/g",
        ]
        with (
            patch(
                "clone.tasks.business_logic.clone_table_create.cmd_run"
            ) as mock_cmd_run,
            patch(
                "clone.tasks.business_logic.clone_table_create.fix_corrupted_utf8_file"
            ) as mock_fix,
            patch("clone.tasks.business_logic.clone_table_create.TMP_FOLDER", "/tmp"),
        ):
            commands_download_to_disk_first(
                data_endpoint=AnyUrl(url="https://example.com/adresses-france.csv.gz"),
                file_downloaded="adresses-france.csv.gz",
                file_unpacked="adresses-france.csv",
                delimiter=";",
                convert_downloaded_file_to_utf8=False,
                fix_corrupted_utf8_sed_substitutions=substitutions,
                table_name="my_table",
                dry_run=True,
            )
            assert len(mock_cmd_run.call_args_list) == 4
            mock_fix.assert_called_once()
            assert mock_fix.call_args.kwargs["sed_substitutions"] == substitutions
