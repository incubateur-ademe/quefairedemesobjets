from clone.tasks.business_logic.clone_table_create import (
    csv_url_to_commands,
    table_schema_get,
)
from rich import print

from dags.clone.config import TABLES


class TestTableSchemaGet:

    def test_unite(self):
        sql = table_schema_get(TABLES.UNITE.kind, "my_unite")
        assert "DROP TABLE" not in sql  # we create new timestamped tables each time
        assert "CREATE TABLE my_unite" in sql

    def test_etab(self):
        sql = table_schema_get(TABLES.ETAB.kind, "my_etab")
        assert "DROP TABLE" not in sql
        assert "CREATE TABLE my_etab" in sql


class TestCsvUrlToCommands:

    def test_zip(self):
        commands = csv_url_to_commands(
            # Testing a case similar to Annuaire Entreprises where
            # the URL filename doesn't match the extracted filename
            # (StockUniteLegale_utf8.zip -> StockUniteLegale_utf8.csv)
            csv_url="https://example.com/StockUniteLegale_utf8.zip",
            csv_downloaded="StockUniteLegale_utf8.zip",
            csv_unpacked="StockUniteLegale_utf8.csv",
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
            csv_url="https://example.com/adresses-france.csv.gz",
            csv_downloaded="adresses-france.csv.gz",
            csv_unpacked="adresses-france.csv",
            table_name="my_table",
        )
        print(commands)
        assert len(commands) == 3
