import logging
import subprocess
import tempfile

from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()


def switch_tables(cursor, prefix_django, prefix_dbt, tables):
    logger.warning("Switch tables")
    logger.warning("Open a transaction")
    cursor.execute("BEGIN")
    try:
        for table in tables:
            logger.warning(
                f"Renaming {prefix_django}{table} to {prefix_django}{table}_to_remove"
            )
            cursor.execute(
                f"ALTER TABLE IF EXISTS {prefix_django}{table}"
                f" RENAME TO {prefix_django}{table}_to_remove"
            )
            logger.warning(f"Renaming {prefix_dbt}{table} to {prefix_django}{table}")
            cursor.execute(
                f"ALTER TABLE {prefix_dbt}{table} RENAME TO {prefix_django}{table}"
            )
            logger.warning(f"Removing {prefix_django}{table}_to_remove")
            cursor.execute(
                f"DROP TABLE IF EXISTS {prefix_django}{table}_to_remove CASCADE"
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
    from django.db import connection

    with connection.cursor() as cursor:
        copy_table_with_fdw(cursor, prefix_dbt, tables)
        switch_tables(cursor, prefix_django, prefix_dbt, tables)


def get_warehouse_connection_info():
    from django.conf import settings

    warehouse = settings.DATABASES["warehouse"]
    return {
        "HOST": warehouse.get("HOST", "localhost"),
        "PORT": warehouse.get("PORT", "5432"),
        "DB": warehouse["NAME"],
        "USER": warehouse["USER"],
        "PASSWORD": warehouse["PASSWORD"],
    }


def copy_table_with_fdw(cursor, prefix, tables):
    warehouse = get_warehouse_connection_info()

    try:
        # Step 1: Enable FDW
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgres_fdw;")

        # Step 2: Drop/recreate FDW server
        cursor.execute("DROP SERVER IF EXISTS warehouse_fdw CASCADE;")
        cursor.execute(
            f"""
            CREATE SERVER warehouse_fdw
            FOREIGN DATA WRAPPER postgres_fdw
            OPTIONS (
                host '{warehouse.get('HOST')}',
                dbname '{warehouse.get('DB')}',
                port '{warehouse.get('PORT')}'
            );
        """
        )

        # Step 3: Create user mapping
        cursor.execute(
            f"""
            CREATE USER MAPPING FOR CURRENT_USER
            SERVER warehouse_fdw
            OPTIONS (
                user '{warehouse["USER"]}',
                password '{warehouse["PASSWORD"]}'
            );
        """
        )

        # Step 4: Import the table into a foreign schema
        prefixed_tables = [f"{prefix}{table}" for table in tables]
        limit_to_clause = ", ".join(prefixed_tables)
        tmp_schema = "warehouse_import"
        cursor.execute(
            f"""
            CREATE SCHEMA {tmp_schema};
            """
        )
        cursor.execute(
            f"""
            IMPORT FOREIGN SCHEMA public
            LIMIT TO ({limit_to_clause})
            FROM SERVER warehouse_fdw
            INTO {tmp_schema};
        """
        )

        # Step 5: Copy each table
        for table in tables:
            # logger.info(f"Deleting table '{table}'...")
            # cursor.execute(f"DELETE FROM {table};")
            logger.info(f"Copying table '{table}'...")
            cursor.execute(
                f"""
                INSERT INTO {table}
                SELECT * FROM warehouse_import.{table};
            """
            )
            logger.info(f"Finished copying table '{table}'.")

        cursor.execute(
            f"""
            DROP SCHEMA {tmp_schema};
            """
        )
        logger.info("All tables copied successfully using FDW.")

    except Exception as e:
        logger.error(f"Error copying table {tables} via FDW: {e}")
        raise


def copy_table_with_pg_tools(table):
    from django.conf import settings

    warehouse_connection = settings.DB_WAREHOUSE
    qfdmo_connection = settings.DATABASE_URL

    logger.info(f"Copying table {table} using pg_dump/pg_restore")
    try:
        with tempfile.NamedTemporaryFile() as tmpfile:
            dump_file_path = tmpfile.name

            pg_dump_cmd = [
                "pg_dump",
                "--format",
                "custom",
                "--large-objects",
                "--table",
                table,
                "--dbname",
                warehouse_connection,
                "--file",
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
