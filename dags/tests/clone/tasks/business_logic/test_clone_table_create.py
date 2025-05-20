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
        sql = sql.replace(r"{{db_schema}}", "my_schema")
        # We DON'T drop tables during creation as they are versioned
        assert "DROP TABLE" not in sql
        assert "CREATE TABLE my_schema.my_table" in sql


class TestCommands:

    def test_stream_zip(self):
        # Stream a file directly to DB
        cmds_create, cmd_cleanup = commands_stream_directly(
            data_endpoint=AnyUrl(url="https://example.com/StockUniteLegale_utf8.zip"),
            delimiter=",",
            db_schema="my_schema",
            table_name="my_table",
        )
        assert len(cmds_create) == 1
        assert all(x in cmds_create[0]["cmd"] for x in ["curl", "zcat", "psql"])
        assert "rm -rf" not in cmd_cleanup["cmd"]
        assert "echo" in cmd_cleanup["cmd"]

    def test_download_zip(self):
        cmds_create, cmd_cleanup = commands_download_to_disk_first(
            # Testing a case similar to Annuaire Entreprises where
            # the URL filename doesn't match the extracted filename
            # (StockUniteLegale_utf8.zip -> StockUniteLegale_utf8.csv)
            data_endpoint=AnyUrl(url="https://example.com/StockUniteLegale_utf8.zip"),
            file_downloaded="StockUniteLegale_utf8.zip",
            file_unpacked="StockUniteLegale_utf8.csv",
            delimiter=",",
            db_schema="my_schema",
            table_name="my_table",
        )
        assert len(cmds_create) == 5
        assert "mkdir" in cmds_create[0]["cmd"]
        assert "curl" in cmds_create[1]["cmd"]
        assert "unzip" in cmds_create[2]["cmd"]
        assert "wc" in cmds_create[3]["cmd"]
        assert "psql" in cmds_create[4]["cmd"]
        assert "rm -rf" in cmd_cleanup["cmd"]

    def test_download_gz(self):
        cmds_create, cmd_cleanup = commands_download_to_disk_first(
            data_endpoint=AnyUrl(url="https://example.com/adresses-france.csv.gz"),
            file_downloaded="adresses-france.csv.gz",
            file_unpacked="adresses-france.csv",
            delimiter=";",
            db_schema="my_schema",
            table_name="my_table",
        )
        assert len(cmds_create) == 5
        assert "mkdir" in cmds_create[0]["cmd"]
        assert "curl" in cmds_create[1]["cmd"]
        assert "gunzip" in cmds_create[2]["cmd"]
        assert "wc" in cmds_create[3]["cmd"]
        assert "psql" in cmds_create[4]["cmd"]
        assert "rm -rf" in cmd_cleanup["cmd"]
