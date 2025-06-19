import logging
import subprocess
import tempfile

from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()


def switch_tables(cursor, prefix_django, prefix_dbt, tables):
    # pg_dump -Fc -b -t MA_TABLE DB1|pg_restore -h localhost -d DB2

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


def replace_acteur_table(
    prefix_django: str,
    prefix_dbt: str,
    tables=[
        "acteur",
        "acteur_acteur_services",
        "acteur_labels",
        "acteur_sources",
        "propositionservice",
        "propositionservice_sous_categories",
    ],
):
    from django.db import DEFAULT_DB_ALIAS, connections

    for table in tables:
        copy_table_with_pg_tools(f"{prefix_dbt}{table}")

    with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
        switch_tables(cursor, prefix_django, prefix_dbt, tables)


def copy_table_with_pg_tools(table):
    from django.conf import settings

    warehouse_connection = settings.DB_WAREHOUSE
    qfdmo_connection = settings.DATABASE_URL

    logger.warning(f"Copying table {table} using pg_dump/pg_restore")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            dump_file_path = tmpfile.name

            pg_dump_cmd = [
                "pg_dump",
                "-Fc",  # Format custom
                "-b",  # Include blobs
                "-t",
                table,  # Table spécifique
                "-d",
                warehouse_connection,
                "-f",
                dump_file_path,
            ]

            subprocess.run(pg_dump_cmd)

            pg_restore_cmd = [
                "pg_restore",
                "-d",
                qfdmo_connection,
                "--clean",
                "--if-exists",
                "--no-comments",
                "--disable-triggers",
                "--no-owner",
                "--no-privileges",
                dump_file_path,
            ]

            subprocess.run(pg_restore_cmd)
            logger.warning(f"Successfully copied table {table}, using {dump_file_path}")

    except Exception as e:
        logger.error(f"Error copying table {table}: {str(e)}")
        raise
