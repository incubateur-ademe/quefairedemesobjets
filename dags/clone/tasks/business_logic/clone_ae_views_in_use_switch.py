from clone.tasks.business_logic.clone_ae_table_create import schema_create_and_check


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

    sql = f"""CREATE OR REPLACE VIEW {view_name_unite} AS
    SELECT * FROM {table_name_unite}"""

    schema_create_and_check(schema_name=table_name_unite, sql=sql, dry_run=dry_run)

    sql = f"""CREATE OR REPLACE VIEW {view_name_etab} AS
    SELECT * FROM {table_name_etab}"""

    schema_create_and_check(schema_name=table_name_etab, sql=sql, dry_run=dry_run)
