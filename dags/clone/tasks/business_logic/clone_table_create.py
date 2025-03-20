"""Creates the actual tables replicating AE in our DB"""

import logging

from clone.config import DIR_SQL_SCHEMAS
from utils import logging_utils as log
from utils.cmd import cmd_run
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def csv_url_to_commands(
    csv_url: str, csv_downloaded, csv_unpacked: str, table_name
) -> list[dict]:
    """Generates a list of commands to run to replicate the data locally"""
    from django.db import connection

    # Initial setup
    db = connection.settings_dict
    results = []

    # Starting with commands which don't require the DB
    cmds = []
    cmds.append(f"curl -sSL {csv_url} -o /tmp/{csv_downloaded}")
    if csv_url.endswith(".zip"):
        cmds.append(f"unzip /tmp/{csv_downloaded} -d /tmp/{csv_unpacked}")
    elif csv_url.endswith(".gz"):
        cmds.append(f"gunzip -c /tmp/{csv_downloaded} > /tmp/{csv_unpacked}")
    elif csv_url.endswith(".csv"):
        pass
    else:
        raise NotImplementedError(f"URL non supportée: {csv_url}")
    # Converting commands so far into results format
    results.extend([{"cmd": cmd, "env": {}} for cmd in cmds])

    # Finally the command to load the CSV into the DB
    results.append(
        {
            "cmd": (
                f"cat /tmp/{csv_unpacked} | "
                f"psql -h {db['HOST']} -p {db['PORT']} -U {db['USER']} -d {db['NAME']} "
                f"-c '\\copy {table_name} FROM stdin WITH (FORMAT csv, HEADER true)'"
            ),
            "env": {"PGPASSWORD": db["PASSWORD"]},
        }
    )

    return results


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
    csv_url: str,
    csv_downloaded: str,
    csv_unpacked: str,
    table_name: str,
    dry_run: bool = False,
):
    r"""Streams a CSV from a URL directly into a PG.
    🔴 Requires the table schema to be created prior to this"""
    commands = csv_url_to_commands(
        csv_url=csv_url,
        csv_downloaded=csv_downloaded,
        csv_unpacked=csv_unpacked,
        table_name=table_name,
    )
    for command in commands:
        cmd_run(command["cmd"], env=command["env"], dry_run=dry_run)


def clone_ae_table_create(
    csv_url: str,
    csv_downloaded: str,
    csv_unpacked: str,
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
        csv_downloaded=csv_downloaded,
        csv_unpacked=csv_unpacked,
        table_name=table_name,
        dry_run=dry_run,
    )

    # Final log
    logger.info(log.banner_string("🏁 Résultat final de la tâche"))
    logger.info(f"Nom de le table: {table_name}")
    log.preview("Schema obtenu", sql)
    logger.info("Création schema: " + "✋ (dry_run)" if dry_run else "🟢 effectuée")
    logger.info("Chargement CSV: " + "✋ (dry_run)" if dry_run else "🟢 effectué")
