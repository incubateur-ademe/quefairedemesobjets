"""Creates the actual tables replicating AE in our DB"""

import logging
import tempfile
from pathlib import Path

from pydantic import AnyUrl
from shared.config.airflow import TMP_FOLDER
from utils import logging_utils as log
from utils.cmd import cmd_run
from utils.django import django_schema_create_and_check, django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def command_psql_copy_from_csv(
    table_name: str,
    delimiter: str,
) -> str:
    """Command to load CSV into DB, factored out for reuse"""
    from django.conf import settings

    db_dsn = settings.DB_WAREHOUSE
    cmd_from = f'stdin WITH (FORMAT csv, HEADER true, DELIMITER "{delimiter}");'
    cmd = f"psql -d '{db_dsn}' -c '\\copy {table_name} FROM {cmd_from}'"
    return cmd


def command_ogr2ogr_import_geojson(
    table_name: str,
    geojson_file_path: str,
    geometry_column_name: str = "contours_administratifs",
) -> str:
    """Command to load GeoJSON into DB using ogr2ogr, factored out for reuse"""
    from django.conf import settings

    warehouse_db_settings = settings.DATABASES["warehouse"]

    # Build PostgreSQL connection string for ogr2ogr
    # Format: PG:"dbname=name user=user password=pass host=host port=port"
    pg_connection_string = (
        f'PG:"dbname={warehouse_db_settings["NAME"]} '
        f'user={warehouse_db_settings["USER"]} '
        f'password={warehouse_db_settings["PASSWORD"]} '
        f'host={warehouse_db_settings["HOST"]} '
        f'port={warehouse_db_settings["PORT"]}"'
    )

    cmd = (
        f'ogr2ogr -f "PostgreSQL" {pg_connection_string} '
        f"-overwrite "
        f"-lco GEOMETRY_NAME={geometry_column_name} "
        f"-lco FID=id "
        f"-lco PRECISION=NO "
        f"-nln {table_name} "
        f"{geojson_file_path}"
    )
    return cmd


def commands_stream_directly(
    data_endpoint: AnyUrl,
    delimiter: str,
    table_name: str,
    dry_run: bool,
):
    """Commands to create table while streaming directly to DB (no disk)"""

    logger.info("Pas de nettoyage requis en streaming")

    cmd_psql = command_psql_copy_from_csv(table_name=table_name, delimiter=delimiter)
    if str(data_endpoint).endswith(".gz") or str(data_endpoint).endswith(".zip"):
        cmd_run(f"curl -s '{data_endpoint}' | zcat | {cmd_psql}", dry_run=dry_run)
    else:
        cmd_run(f"curl -s '{data_endpoint}' | {cmd_psql}", dry_run=dry_run)


def commands_download_to_disk_first(
    data_endpoint: AnyUrl,
    file_downloaded: str,
    file_unpacked: str | None,
    delimiter: str,
    table_name: str,
    convert_downloaded_file_to_utf8: bool,
    dry_run: bool,
):
    """Commands to create table while first dowloading to disk"""

    file_unpacked = file_unpacked or file_downloaded

    # File download and unpacking: all done within a temporary folder
    # so cleanup is easier AND to avoid collisions (table name contains timestamp)
    with tempfile.TemporaryDirectory(dir=TMP_FOLDER) as folder:
        # Download to folder
        cmd_run(
            f"curl -sSL {data_endpoint} -o {folder}/{file_downloaded}", dry_run=dry_run
        )

        # Unpack the file
        if str(file_downloaded).endswith(".zip"):
            cmd_run(f"unzip {folder}/{file_downloaded} -d {folder}/", dry_run=dry_run)
        if str(file_downloaded).endswith(".gz"):
            cmd_run(
                f"gunzip -c {folder}/{file_downloaded} > {folder}/{file_unpacked}",
                dry_run=dry_run,
            )

        # Check the unpacked file
        cmd_run(f"wc -l {folder}/{file_unpacked}", dry_run=dry_run)

        # Convert to UTF-8 if needed
        if convert_downloaded_file_to_utf8:
            file_converted = file_unpacked.replace(".csv", "_utf8.csv")
            cmd_run(
                "iconv -f ISO-8859-1 -t UTF-8"
                f" {folder}/{file_unpacked} > {folder}/{file_converted}",
                dry_run=dry_run,
            )
            file_unpacked = file_converted

        # Load into DB
        if file_unpacked.endswith(".csv"):
            cmd_psql = command_psql_copy_from_csv(
                table_name=table_name, delimiter=delimiter
            )
            cmd_run(f"cat {folder}/{file_unpacked} | {cmd_psql}", dry_run=dry_run)
        elif file_unpacked.endswith(".geojson"):
            geojson_file_path = f"{folder}/{file_unpacked}"
            cmd_ogr2ogr = command_ogr2ogr_import_geojson(
                table_name=table_name, geojson_file_path=geojson_file_path
            )
            cmd_run(cmd_ogr2ogr, dry_run=dry_run)
        else:
            raise ValueError(f"File {file_unpacked} has an invalid extension")


def clone_table_create(
    data_endpoint: AnyUrl,
    clone_method: str,
    file_downloaded: str | None,
    file_unpacked: str | None,
    delimiter: str,
    table_name: str,
    table_schema_file_path: Path,
    convert_downloaded_file_to_utf8: bool,
    dry_run: bool,
) -> None:
    from django.db import connections

    """Create a table in the DB from a CSV file downloaded via URL"""

    # Force download_to_disk_first for GeoJSON files
    if str(data_endpoint).endswith(".geojson.gz") or str(data_endpoint).endswith(
        ".geojson"
    ):
        clone_method = "download_to_disk_first"

    logger.info(log.banner_string(f"Création du schema de la table {table_name}"))

    try:
        # Create table schema to hold the data
        sql = (
            table_schema_file_path.read_text()
            .replace(r"{{table_name}}", table_name)
            .replace(r"{{db_schema}}", "public")
        )
        django_schema_create_and_check(table_name, sql, dry_run=dry_run)

        # Get commands based on the create method
        if clone_method == "download_to_disk_first":
            if file_downloaded is None:
                raise ValueError(
                    "file_downloaded is required for download_to_disk_first"
                )

            commands_download_to_disk_first(
                data_endpoint=data_endpoint,
                file_downloaded=file_downloaded,
                file_unpacked=file_unpacked,
                delimiter=delimiter,
                table_name=table_name,
                convert_downloaded_file_to_utf8=convert_downloaded_file_to_utf8,
                dry_run=dry_run,
            )
        elif clone_method == "stream_directly":
            commands_stream_directly(
                data_endpoint=data_endpoint,
                delimiter=delimiter,
                table_name=table_name,
                dry_run=dry_run,
            )
        else:
            raise ValueError(f"Méthode {clone_method=} invalide")

        # Final log
        logger.info(log.banner_string("🏁 Résultat final de la tâche"))
        logger.info(f"Nom de le table: {table_name}")
        log.preview("Schema obtenu", sql)
        logger.info("Création schema: " + "✋ (dry_run)" if dry_run else "🟢 effectuée")
        logger.info("Chargement CSV: " + "✋ (dry_run)" if dry_run else "🟢 effectué")

    # If anything went wrong = delete schema if it exists
    except Exception as e:
        logger.error(log.banner_string(f"❌ Erreur rencontrée: {e}"))
        logger.error(f"On supprime la table {table_name} si créée")
        connection = connections["warehouse"]
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        raise e
