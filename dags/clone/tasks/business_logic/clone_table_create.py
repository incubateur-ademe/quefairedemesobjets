"""Creates the actual tables replicating AE in our DB"""

import logging
from pathlib import Path

from pydantic import AnyHttpUrl
from utils import logging_utils as log
from utils.cmd import cmd_run
from utils.django import django_schema_create_and_check, django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def csv_url_to_commands(
    data_endpoint: str,
    file_downloaded: str,
    file_unpacked: str,
    delimiter: str,
    table_name: str,
) -> tuple[list[dict], dict]:
    """Generates a list of commands to run to replicate the data locally"""
    from django.db import connection

    # File download and unpacking: all done within a temporary folder
    # so cleanup is easier AND to avoid collisions (table name contains timestamp)
    folder = f"/tmp/{table_name}"
    cmds_create = []
    cmds_create.append(f"mkdir {folder}")
    cmds_create.append(f"curl -sSL {data_endpoint} -o {folder}/{file_downloaded}")
    if str(data_endpoint).endswith(".zip"):
        cmds_create.append(f"unzip {folder}/{file_downloaded} -d {folder}/")
    elif str(data_endpoint).endswith(".gz"):
        cmds_create.append(
            f"gunzip -c {folder}/{file_downloaded} > {folder}/{file_unpacked}"
        )
    elif str(data_endpoint).endswith(".csv"):
        pass
    else:
        raise NotImplementedError(f"URL non supportée: {data_endpoint}")
    cmds_create.append(f"wc -l {folder}/{file_unpacked}")

    # Converting commands so far into results format
    cmds_create = [{"cmd": cmd, "env": {}} for cmd in cmds_create]

    # Finally the command to load the CSV into the DB
    db = connection.settings_dict
    cmd_from = f'stdin WITH (FORMAT csv, HEADER true, DELIMITER "{delimiter}");'
    cmds_create.append(
        {
            "cmd": (
                f"cat {folder}/{file_unpacked} | "
                f"psql -h {db['HOST']} -p {db['PORT']} -U {db['USER']} -d {db['NAME']} "
                f"-c '\\copy {table_name} FROM {cmd_from}'"
            ),
            "env": {"PGPASSWORD": db["PASSWORD"]},
        }
    )

    # Cleanup
    cmd_cleanup = {"cmd": f"rm -rf {folder}", "env": {}}

    return cmds_create, cmd_cleanup


def csv_from_url_to_table(
    data_endpoint: AnyHttpUrl,
    file_downloaded: str,
    file_unpacked: str,
    delimiter: str,
    table_name: str,
    run_timestamp: str,
    dry_run: bool,
):
    r"""Streams a CSV from a URL directly into a PG.
    🔴 Requires the table schema to be created prior to this"""
    cmds_create, cmd_cleanup = csv_url_to_commands(
        data_endpoint=data_endpoint,
        file_downloaded=file_downloaded,
        file_unpacked=file_unpacked,
        delimiter=delimiter,
        table_name=table_name,
    )

    # Trying creation commands
    error = None
    for command in cmds_create:
        try:
            cmd_run(command["cmd"], env=command["env"], dry_run=dry_run)
        except Exception as e:
            logger.error(e)
            error = str(e)
            break

    # Cleanup: always performing to avoid leaving a mess on server
    cmd_run(cmd_cleanup["cmd"], env=cmd_cleanup["env"], dry_run=dry_run)

    if error:
        raise SystemError(f"Erreur rencontrée: {error}")


def clone_table_create(
    data_endpoint: AnyHttpUrl,
    file_downloaded: str,
    file_unpacked: str,
    delimiter: str,
    table_name: str,
    table_schema_file_path: Path,
    run_timestamp: str,
    dry_run: bool,
) -> None:
    """Create a table in the DB from a CSV file downloaded via URL"""

    # Read tasks
    logger.info(log.banner_string(f"Création du schema de la table {table_name}"))
    sql = table_schema_file_path.read_text().replace(r"{{table_name}}", table_name)

    # Write tasks
    django_schema_create_and_check(table_name, sql, dry_run=dry_run)
    csv_from_url_to_table(
        data_endpoint=data_endpoint,
        file_downloaded=file_downloaded,
        file_unpacked=file_unpacked,
        delimiter=delimiter,
        table_name=table_name,
        run_timestamp=run_timestamp,
        dry_run=dry_run,
    )

    # Final log
    logger.info(log.banner_string("🏁 Résultat final de la tâche"))
    logger.info(f"Nom de le table: {table_name}")
    log.preview("Schema obtenu", sql)
    logger.info("Création schema: " + "✋ (dry_run)" if dry_run else "🟢 effectuée")
    logger.info("Chargement CSV: " + "✋ (dry_run)" if dry_run else "🟢 effectué")
