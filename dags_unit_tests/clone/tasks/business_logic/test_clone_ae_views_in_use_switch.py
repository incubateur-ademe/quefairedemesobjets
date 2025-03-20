from clone.tasks.business_logic.clone_view_in_use_switch import view_schema_get

from dags.clone.config import VIEW_NAME_ETAB, VIEW_NAME_UNITE


class TestTableSchemaGet:

    def test_unite(self):
        sql = view_schema_get(VIEW_NAME_UNITE, "my_unite")
        assert "DROP VIEW" in sql
        assert f"CREATE VIEW {VIEW_NAME_UNITE}" in sql
        assert "FROM my_unite" in sql

    def test_etab(self):
        sql = view_schema_get(VIEW_NAME_ETAB, "my_etab")
        assert "DROP VIEW" in sql
        assert f"CREATE VIEW {VIEW_NAME_ETAB}" in sql
        assert "FROM my_etab" in sql
