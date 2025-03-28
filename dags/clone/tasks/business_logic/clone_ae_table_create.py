"""Creates the actual tables replicating AE in our DB"""

import logging

from clone.config import DIR_SQL_SCHEMAS
from pydantic.networks import AnyHttpUrl
from utils import logging_utils as log
from utils.cmd import cmd_run
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def table_schema_get(table_kind: str, table_name: str) -> str:
    """Get schema for a table kind while replacing its placeholder name"""
    path = DIR_SQL_SCHEMAS / "tables" / f"schema_table_ae_{table_kind}.sql"
    return path.read_text().replace(r"{{table_name}}", table_name)


# TODO: move to utils/django.py
def schema_create_and_check(schema_name: str, sql: str, dry_run=True) -> None:
    """Create a table in the DB from a schema"""
    from django.db import connection

    # Creation
    logger.info(f"Création schema pour {schema_name=}: début")
    log.preview("Schema", sql)
    if dry_run:
        logger.info("Mode dry-run, on ne crée pas le schema")
        return
    with connection.cursor() as cursor:
        cursor.execute(sql)

    # Validation
    tables_all = connection.introspection.table_names()
    if schema_name not in tables_all:
        raise SystemError(f"Table pas crée malgré execution SQL OK: {schema_name}")
    logger.info(f"Création schema pour {schema_name=}: succès 🟢")


def csv_from_url_to_table(
    csv_url: AnyHttpUrl, csv_filestem: str, table_name: str, dry_run: bool = False
):
    r"""Streams a CSV from a remote ZIP file directly into a PG.
    🔴 Requires the table schema to be created prior to this"""
    from django.db import connection

    # DB settings
    db = connection.settings_dict
    db_env = {"PGPASSWORD": db["PASSWORD"]}  # to hide from cmd
    cmd_psql = f"psql -h {db['HOST']} -p {db['PORT']} -U {db['USER']} -d {db['NAME']}"

    cmd_fs_cleanup = f"rm -f /tmp/{csv_filestem}.zip && rm -f /tmp/{csv_filestem}.csv"
    cmd_download = f"curl -sSL {csv_url} -o /tmp/{csv_filestem}.zip"
    cmd_unzip = f"unzip /tmp/{csv_filestem}.zip -d /tmp/"
    cmd_psql = (
        f"cat /tmp/{csv_filestem}.csv | "
        f"psql -h {db['HOST']} -p {db['PORT']} -U {db['USER']} -d {db['NAME']} "
        f"-c '\\copy {table_name} FROM stdin WITH (FORMAT csv, HEADER true)'"
    )

    cmd_run(cmd=cmd_fs_cleanup, dry_run=dry_run)
    cmd_run(cmd=cmd_download, dry_run=dry_run)
    cmd_run(cmd=cmd_unzip, dry_run=dry_run)
    cmd_run(cmd=cmd_psql, dry_run=dry_run, env=db_env)
    cmd_run(cmd=cmd_fs_cleanup, dry_run=dry_run)


def clone_ae_table_create(
    csv_url: AnyHttpUrl,
    csv_filestem: str,
    table_kind: str,
    table_name: str,
    dry_run: bool = True,
    sql: str | None = None,
) -> None:
    """Create a table in the DB from a CSV file downloaded via URL"""

    # Read tasks
    logger.info(log.banner_string(f"Création du schema de la table {table_name}"))
    if not sql:
        sql = table_schema_get(table_kind, table_name)

    # Write tasks
    schema_create_and_check(table_name, sql, dry_run=dry_run)
    csv_from_url_to_table(
        csv_url=csv_url,
        csv_filestem=csv_filestem,
        table_name=table_name,
        dry_run=dry_run,
    )

    # Final log
    logger.info(log.banner_string("🏁 Résultat final de la tâche"))
    logger.info(f"Nom de le table: {table_name}")
    log.preview("Schema obtenu", sql)
    logger.info("Création schema: " + "✋ (dry_run)" if dry_run else "🟢 effectuée")
    logger.info("Chargement CSV: " + "✋ (dry_run)" if dry_run else "🟢 effectué")
