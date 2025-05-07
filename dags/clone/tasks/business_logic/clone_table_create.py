"""Creates the actual tables replicating AE in our DB"""

import logging
from pathlib import Path

from pydantic import AnyUrl

from utils import logging_utils as log
from utils.cmd import cmd_run
from utils.django import django_schema_create_and_check, django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def command_psql_copy(
    db_schema: str,
    table_name: str,
    delimiter: str,
) -> tuple[str, dict]:
    """Command to load CSV into DB, factored out for reuse"""
    from django.db import connection

    db = connection.settings_dict
    cmd_from = f'stdin WITH (FORMAT csv, HEADER true, DELIMITER "{delimiter}");'
    cmd = (
        f"psql -h {db['HOST']} -p {db['PORT']} -U {db['USER']} -d {db['NAME']} "
        f"-c '\\copy {db_schema}.{table_name} FROM {cmd_from}'"
    )
    env = {"PGPASSWORD": db["PASSWORD"]}
    return cmd, env


def commands_stream_directly(
    data_endpoint: AnyUrl,
    delimiter: str,
    db_schema: str,
    table_name: str,
) -> tuple[list[dict], dict]:
    """Commands to create table while streaming directly to DB (no disk)"""

    cmds_create = []
    cmd_cleanup = {"cmd": "echo 'Pas de nettoyage requis en streaming'", "env": {}}

    cmd_psql, env_psql = command_psql_copy(
        db_schema=db_schema, table_name=table_name, delimiter=delimiter
    )
    cmds_create.append(
        {
            "cmd": (f"curl -s {data_endpoint} | " "zcat | " f"{cmd_psql}"),
            "env": env_psql,
        }
    )

    return cmds_create, cmd_cleanup


def commands_download_to_disk_first(
    data_endpoint: AnyUrl,
    file_downloaded: str,
    file_unpacked: str,
    delimiter: str,
    db_schema: str,
    table_name: str,
) -> tuple[list[dict], dict]:
    """Commands to create table while first dowloading to disk"""

    # File download and unpacking: all done within a temporary folder
    # so cleanup is easier AND to avoid collisions (table name contains timestamp)
    folder = f"/tmp/{table_name}"
    cmds_create = []

    # Create folder to hold temporary files
    cmds_create.append(f"mkdir {folder}")

    # Download to folder
    cmds_create.append(f"curl -sSL {data_endpoint} -o {folder}/{file_downloaded}")

    # Unpack the file
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

    # Check the unpacked file
    cmds_create.append(f"wc -l {folder}/{file_unpacked}")

    # Convert commands so far into results format
    cmds_create = [{"cmd": cmd, "env": {}} for cmd in cmds_create]

    # Load into DB
    cmd_psql, env_psql = command_psql_copy(
        db_schema=db_schema, table_name=table_name, delimiter=delimiter
    )
    cmds_create.append(
        {
            "cmd": (f"cat {folder}/{file_unpacked} | " f"{cmd_psql}"),
            "env": env_psql,
        }
    )

    # Cleanup
    cmd_cleanup = {"cmd": f"rm -rf {folder}", "env": {}}

    return cmds_create, cmd_cleanup


def commands_run(
    cmds_create: list[dict],
    cmd_cleanup: dict,
    dry_run: bool,
):

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
    data_endpoint: AnyUrl,
    clone_method: str,
    file_downloaded: str,
    file_unpacked: str,
    delimiter: str,
    db_schema: str,
    table_name: str,
    table_schema_file_path: Path,
    dry_run: bool,
) -> None:
    """Create a table in the DB from a CSV file downloaded via URL"""

    logger.info(log.banner_string(f"Création du schema de la table {table_name}"))

    try:
        # Create table schema to hold the data
        sql = (
            table_schema_file_path.read_text()
            .replace(r"{{table_name}}", table_name)
            .replace(r"{{db_schema}}", db_schema)
        )
        django_schema_create_and_check(table_name, sql, dry_run=dry_run)

        # Get commands based on the create method
        if clone_method == "download_to_disk_first":
            cmds_create, cmd_cleanup = commands_download_to_disk_first(
                data_endpoint=data_endpoint,
                file_downloaded=file_downloaded,
                file_unpacked=file_unpacked,
                delimiter=delimiter,
                db_schema=db_schema,
                table_name=table_name,
            )
        elif clone_method == "stream_directly":
            cmds_create, cmd_cleanup = commands_stream_directly(
                data_endpoint=data_endpoint,
                delimiter=delimiter,
                db_schema=db_schema,
                table_name=table_name,
            )
        else:
            raise ValueError(f"Méthode {clone_method=} invalide")

        # Run the commands
        commands_run(
            cmds_create=cmds_create,
            cmd_cleanup=cmd_cleanup,
            dry_run=dry_run,
        )

        # Final log
        logger.info(log.banner_string("🏁 Résultat final de la tâche"))
        logger.info(f"Nom de le table: {table_name}")
        log.preview("Schema obtenu", sql)
        logger.info("Création schema: " + "✋ (dry_run)" if dry_run else "🟢 effectuée")
        logger.info("Chargement CSV: " + "✋ (dry_run)" if dry_run else "🟢 effectué")

    # If anything went wrong = delete schema if it exists
    except Exception as e:
        from django.db import connection

        logger.error(log.banner_string(f"❌ Erreur rencontrée: {e}"))
        logger.error(f"On supprime la table {db_schema}.{table_name} si créée")
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {db_schema}.{table_name};")
