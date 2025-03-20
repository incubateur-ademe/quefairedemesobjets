from clone.config import DIR_SQL_SCHEMAS, SCHEMAS_PREFIX, VIEW_IN_USE_SUFFIX
from clone.tasks.business_logic.clone_table_create import schema_create_and_check


def view_name_get(kind: str) -> str:
    """Get view name for a table kind"""
    return f"{SCHEMAS_PREFIX}_{kind}_{VIEW_IN_USE_SUFFIX}"


def view_schema_get(view_name: str, table_name: str) -> str:
    """Get schema for a table kind while replacing its placeholder name"""
    path = DIR_SQL_SCHEMAS / "views" / f"schema_view_{view_name}.sql"
    return (
        path.read_text()
        .replace(r"{{view_name}}", view_name)
        .replace(r"{{table_name}}", table_name)
    )


def clone_ae_view_in_use_switch(
    table_kind: str,
    table_name: str,
    dry_run: bool = True,
) -> None:
    """Switching the in-use view to point to the new table"""
    view_name = view_name_get(table_kind)
    sql = view_schema_get(view_name, table_name)
    schema_create_and_check(schema_name=table_name, sql=sql, dry_run=dry_run)
