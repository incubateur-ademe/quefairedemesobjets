import logging
import re

from utils import logging_utils as log
from utils.django import django_setup_full

logger = logging.getLogger(__name__)


def clone_old_tables_remove(
    keep_table_name: str,
    remove_table_name_pattern: re.Pattern,
    dry_run: bool,
) -> None:
    django_setup_full()
    from django.db import connections

    connection = connections["warehouse"]

    # Narrowing down to old tbls to remove
    tbls_all = connection.introspection.table_names()
    tbls_matched = [x for x in tbls_all if remove_table_name_pattern.match(x)]
    tbls_del = [x for x in tbls_matched if x != keep_table_name]

    # Preview
    log.preview("🟢 Table(s) à garder", [keep_table_name])
    log.preview("🟠 Table(s) à supprimer", tbls_del)

    # Removing the old tbls
    for table_name in tbls_del:
        logger.info(f"🔵 Suppression table {table_name}: début")
        if dry_run:
            logger.info("✋ Mode dry-run, on ne supprime pas la table")
            continue
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE {table_name}")
        logger.info(f"🟢 Suppression table {table_name}: succès")
