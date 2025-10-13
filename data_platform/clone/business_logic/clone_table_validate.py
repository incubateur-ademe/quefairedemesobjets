from prefect import task

from data_platform.clone.config.model import DIR_SQL_VALIDATION, CloneConfig
from data_platform.shared.utils import logging_utils as log
from data_platform.shared.utils.django import DJANGO_WH_CONNECTION_NAME


@task(name="Valider la table", retries=3, retry_delay_seconds=10)
def validate_table(config: CloneConfig) -> bool:
    """
    💡 Quoi: valider que la table créée est correcte
    🎯 Pourquoi: s'assurer de la qualité des données avant de les mettre en production
    🏗️ Comment: exécuter les requêtes SQL de validation
    """
    log.warning(f"Validation de la table {config.table_name}")

    clone_table_validate(
        table_kind=config.table_kind,
        table_name=config.table_name,
        dry_run=config.dry_run,
    )
    return True


def clone_table_validate(table_kind: str, table_name: str, dry_run: bool) -> None:
    """Validate a table in the DB"""
    from django.db import connections

    # Gathering SQL validation files
    sql_files = list((DIR_SQL_VALIDATION / table_kind).glob("*.sql"))
    log.preview("Fichiers de validation trouvés", sql_files)

    # Executing SQL validation files
    for sql_file in sql_files:
        sql = sql_file.read_text().replace(r"{{table_name}}", table_name)
        sql_name = sql_file.stem
        log.info(f"🔵 {table_name}: {sql_name} en validation...")
        if dry_run:
            log.info("Mode dry-run, on ne valide pas")
            continue
        with connections[DJANGO_WH_CONNECTION_NAME].cursor() as cursor:
            # Running validation and getting results
            cursor.execute(sql)
            row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, row))
            is_valid = result["is_valid"]
            debug_value = result["debug_value"]

            # Checking results
            if not is_valid:
                raise ValueError(f"{table_name}: {sql_name} échec: {debug_value}")
            log.info(f"🟢 {table_name}: {sql_name} succès: {debug_value}")
