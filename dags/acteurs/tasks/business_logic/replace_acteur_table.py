import logging

from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()


def replace_acteur_table(
    prefix_django: str,
    prefix_dbt: str,
    tables: list[str],
) -> None:
    from django.db import DEFAULT_DB_ALIAS, connections

    with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
        copy_tables_between_servers(cursor, prefix_dbt, prefix_django, tables)
        switch_tables(cursor, prefix_django, prefix_dbt, tables)


def copy_tables_between_servers(cursor, prefix_dbt, prefix_django, tables):
    from django.conf import settings

    cursor.execute("BEGIN")
    try:
        for table in tables:
            logger.warning(
                f"copy table to {prefix_dbt}{table} from warehouse to webapp"
            )

            # Refresh table in webapp_public
            cursor.execute(
                f"DROP FOREIGN TABLE IF EXISTS"
                f" {settings.REMOTE_WAREHOUSE_SCHEMANAME}.{prefix_dbt}{table}"
            )
            cursor.execute(
                f"IMPORT FOREIGN SCHEMA public"
                f" LIMIT TO ({prefix_dbt}{table})"
                f" FROM SERVER {settings.REMOTE_WAREHOUSE_SERVERNAME}"
                f" INTO {settings.REMOTE_WAREHOUSE_SCHEMANAME}"
            )

            # Create table with same structure including indexes
            cursor.execute(f"DROP TABLE IF EXISTS {prefix_dbt}{table}")
            cursor.execute(
                f"CREATE TABLE {prefix_dbt}{table} (LIKE "
                f"{prefix_django}{table} "
                f"INCLUDING INDEXES)"
            )

            # Get column names in correct order
            cursor.execute(
                f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{prefix_django}{table}'
                ORDER BY ordinal_position
            """
            )
            columns = [col[0] for col in cursor.fetchall()]
            columns_str = ", ".join(columns)

            # Copy data
            cursor.execute(
                f"INSERT INTO {prefix_dbt}{table} ({columns_str}) "
                f"SELECT {columns_str} FROM "
                f"{settings.REMOTE_WAREHOUSE_SCHEMANAME}.{prefix_dbt}{table}"
            )

        logger.warning("Commit the transaction")
        cursor.execute("COMMIT")
    except Exception as e:
        logger.warning("Rollback the transaction")
        cursor.execute("ROLLBACK")
        raise e


def switch_tables(cursor, prefix_django, prefix_dbt, tables):

    logger.warning("Switch tables")
    logger.warning("Open a transaction")
    cursor.execute("BEGIN")
    try:
        for table in tables:
            logger.warning(
                f"Renaming {prefix_django}{table}"
                f" to {prefix_django}{table}_to_remove"
            )
            cursor.execute(
                f"ALTER TABLE IF EXISTS {prefix_django}{table}"
                f" RENAME TO {prefix_django}{table}_to_remove"
            )
            logger.warning(f"Renaming {prefix_dbt}{table} to {prefix_django}{table}")
            cursor.execute(
                f"ALTER TABLE {prefix_dbt}{table} RENAME TO" f" {prefix_django}{table}"
            )
            logger.warning(f"Removing {prefix_django}{table}_to_remove")
            cursor.execute(
                f"DROP TABLE IF EXISTS" f" {prefix_django}{table}_to_remove CASCADE"
            )
        logger.warning("Commit the transaction")
        cursor.execute("COMMIT")
    except Exception as e:
        logger.warning("Rollback the transaction")
        cursor.execute("ROLLBACK")
        raise e
