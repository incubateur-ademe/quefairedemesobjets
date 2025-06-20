import pytest
from clone.config import DIR_SQL_CREATION


class TestSqlTablesCreation:

    @pytest.mark.parametrize("path", list((DIR_SQL_CREATION / "views").glob("*.sql")))
    def test_sql_content(self, path):
        # Making sure the key statements are present in the SQL
        sql = path.read_text()
        sql = sql.replace(r"{{view_name}}", "my_view")
        sql = sql.replace(r"{{table_name}}", "my_table")
        assert "DROP TABLE" not in sql
        assert "DROP VIEW IF EXISTS my_view CASCADE" in sql
        assert "CREATE VIEW my_view" in sql
        assert "FROM my_table" in sql
