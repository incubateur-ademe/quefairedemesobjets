from dags.clone.config import TABLES
from dags.clone.tasks.business_logic.clone_ae_table_create import table_schema_get


class TestTableSchemaGet:

    def test_unite(self):
        sql = table_schema_get(TABLES.UNITE.kind, "my_unite")
        assert "DROP TABLE" not in sql  # we create new timestamped tables each time
        assert "CREATE TABLE my_unite" in sql

    def test_etab(self):
        sql = table_schema_get(TABLES.ETAB.kind, "my_etab")
        assert "DROP TABLE" not in sql
        assert "CREATE TABLE my_etab" in sql
