from unittest.mock import patch

import pytest
from clone.config import DIR_SQL_CREATION
from clone.tasks.business_logic.clone_table_create import (
    commands_download_to_disk_first,
    commands_stream_directly,
)
from pydantic import AnyUrl


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
                table_name="my_table",
                dry_run=True,
            )
            assert len(mock_cmd_run.call_args_list) == 4
            assert "curl" in mock_cmd_run.call_args_list[0][0][0]
            assert "zcat" in mock_cmd_run.call_args_list[1][0][0]
            assert "wc" in mock_cmd_run.call_args_list[2][0][0]
            assert "psql" in mock_cmd_run.call_args_list[3][0][0]
