import logging

from clone.config.paths import DIR_SQL_VALIDATIONS
from django.db import connection
from utils.raisers import raise_if

logger = logging.getLogger(__name__)


def clone_ae_table_validate(
    table_kind: str, table_name: str, dry_run: bool = True
) -> None:
    """Validate a table in the DB"""

    # Gathering SQL validation files
    sql_files = list((DIR_SQL_VALIDATIONS / table_kind).glob("*.sql"))
    raise_if(not sql_files, f"{table_kind} / {table_name}: 0 fichier de validation")

    # Executing SQL validation files
    for sql_file in sql_files:
        sql = sql_file.read_text().replace(r"{{table_name}}", table_name)
        sql_name = sql_file.stem
        logger.info(f"🔵 {table_name}: {sql_name} en validation...")
        if dry_run:
            logger.info("Mode dry-run, on ne valide pas")
            continue
        with connection.cursor() as cursor:

            # Running validation and getting results
            cursor.execute(sql)
            row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, row))
            is_valid = result["is_valid"]
            debug_value = result["debug_value"]

            # Checking results
            raise_if(not is_valid, f"🔴 {table_name}: {sql_name} échec: {debug_value}")
            logger.info(f"🟢 {table_name}: {sql_name} succès: {debug_value}")
