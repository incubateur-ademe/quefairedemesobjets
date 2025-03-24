import pytest
from clone.config import DIR_SQL_CREATION
from clone.tasks.business_logic.clone_table_create import (
    csv_url_to_commands,
)
from rich import print


class TestSqlTablesCreation:

    @pytest.mark.parametrize("path", list((DIR_SQL_CREATION / "tables").glob("*.sql")))
    def test_sql_content(self, path):
        # Making sure the key statements are present in the SQL
        sql = path.read_text()
        sql = sql.replace(r"{{table_name}}", "my_table")
        # We DON'T drop tables during creation as they are versioned
        assert "DROP TABLE" not in sql
        assert "CREATE TABLE my_table" in sql


class DISABLEDTestCsvUrlToCommands:

    def test_zip(self):
        commands = csv_url_to_commands(
            # Testing a case similar to Annuaire Entreprises where
            # the URL filename doesn't match the extracted filename
            # (StockUniteLegale_utf8.zip -> StockUniteLegale_utf8.csv)
            data_url="https://example.com/StockUniteLegale_utf8.zip",
            file_downloaded="StockUniteLegale_utf8.zip",
            file_unpacked="StockUniteLegale_utf8.csv",
            delimiter=",",
            table_name="my_table",
        )
        print(commands)
        assert len(commands) == 3
        # only last command has some env
        assert commands[0]["env"] == {}
        assert commands[1]["env"] == {}
        assert commands[2]["env"]["PGPASSWORD"]

    def test_gz(self):
        commands = csv_url_to_commands(
            # Testing case for BAN: adresses-france.csv.gz
            data_url="https://example.com/adresses-france.csv.gz",
            file_downloaded="adresses-france.csv.gz",
            file_unpacked="adresses-france.csv",
            delimiter=";",
            table_name="my_table",
        )
        print(commands)
        assert len(commands) == 3
