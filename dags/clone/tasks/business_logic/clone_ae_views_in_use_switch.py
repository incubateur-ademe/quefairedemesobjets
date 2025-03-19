from clone.config import DIR_SQL_SCHEMAS
from clone.tasks.business_logic.clone_ae_table_create import schema_create_and_check


def view_schema_get(view_name: str, table_name: str) -> str:
    """Get schema for a table kind while replacing its placeholder name"""
    path = DIR_SQL_SCHEMAS / "views" / f"schema_view_{view_name}.sql"
    return (
        path.read_text()
        .replace(r"{{view_name}}", view_name)
        .replace(r"{{table_name}}", table_name)
    )


def clone_ae_views_in_use_switch(
    table_name_unite: str,
    table_name_etab: str,
    view_name_unite: str,
    view_name_etab: str,
    dry_run: bool = True,
) -> None:
    """Switching the views to the new tables. Doing this in a single
    task to prevent inconsistencies & potentially 1 view being switched
    while the other is not"""

    # Unite
    sql = view_schema_get(view_name_unite, table_name_unite)
    schema_create_and_check(schema_name=table_name_unite, sql=sql, dry_run=dry_run)

    # Etab
    sql = view_schema_get(view_name_etab, table_name_etab)
    schema_create_and_check(schema_name=table_name_etab, sql=sql, dry_run=dry_run)
