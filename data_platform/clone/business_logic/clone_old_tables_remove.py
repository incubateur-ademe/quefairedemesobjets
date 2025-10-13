import re

from prefect import task

from data_platform.clone.config.model import CloneConfig
from data_platform.shared.utils import logging_utils as log
from data_platform.shared.utils.django import django_setup_full


@task(name="Supprimer les anciennes tables")
def remove_old_tables(config: CloneConfig) -> None:
    """
    💡 Quoi: supprimer les anciennes tables obsolètes
    🎯 Pourquoi: libérer de l'espace et maintenir la DB propre
    🏗️ Comment: identifier et supprimer les tables qui correspondent au pattern
    """
    log.info(f"Suppression des anciennes tables {config.table_kind}")

    clone_old_tables_remove(
        keep_table_name=config.table_name,
        remove_table_name_pattern=config.table_name_pattern,
        dry_run=config.dry_run,
    )


def clone_old_tables_remove(
    keep_table_name: str,
    remove_table_name_pattern: re.Pattern,
    dry_run: bool,
) -> None:
    django_setup_full()
    from django.db import connection

    # Narrowing down to old tbls to remove
    tbls_all = connection.introspection.table_names()
    tbls_matched = [x for x in tbls_all if remove_table_name_pattern.match(x)]
    tbls_del = [x for x in tbls_matched if x != keep_table_name]

    # Preview
    log.preview("🟢 Table(s) à garder", [keep_table_name])
    log.preview("🟠 Table(s) à supprimer", tbls_del)

    # Removing the old tbls
    for table_name in tbls_del:
        log.info(f"🔵 Suppression table {table_name}: début")
        if dry_run:
            log.info("✋ Mode dry-run, on ne supprime pas la table")
            continue
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE {table_name}")
        log.info(f"🟢 Suppression table {table_name}: succès")
