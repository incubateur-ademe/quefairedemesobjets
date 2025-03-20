import logging

from utils import logging_utils as log
from utils.django import django_setup_full

logger = logging.getLogger(__name__)


def clone_ae_old_tables_remove(
    keep_table_names: list[str],
    keep_view_names: list[str],
    table_prefix: str,
    dry_run: bool = True,
):
    django_setup_full()
    from django.db import connection

    # Narrowing down to old tbls to remove
    tbls_all = connection.introspection.table_names()
    tbls_ea = [x for x in tbls_all if x.startswith(table_prefix)]
    tbls_ea_del = [x for x in tbls_ea if x not in keep_table_names + keep_view_names]

    # Preview
    log.preview("👉 Tables à garder", keep_table_names)
    log.preview("👉 Vues à garder", keep_view_names)
    log.preview("👉 Préfixe des tables", table_prefix)
    log.preview("🟢 Toutes les tables", tbls_all)
    log.preview("🟢 Tables EA", tbls_ea)
    log.preview("🟠 Tables EA à supprimer", tbls_ea_del)

    # Removing the old tbls
    for table_name in tbls_ea_del:
        logger.info(f"🔵 Suppression table {table_name}: début")
        if dry_run:
            logger.info("✋ Mode dry-run, on ne supprime pas la table")
            continue
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE {table_name}")
        logger.info(f"🟢 Suppression table {table_name}: succès")
