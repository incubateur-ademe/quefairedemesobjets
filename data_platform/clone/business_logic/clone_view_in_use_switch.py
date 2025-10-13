from pathlib import Path

from prefect import task

from data_platform.clone.config.model import CloneConfig
from data_platform.shared.utils import logging_utils as log
from data_platform.shared.utils.django import django_schema_create_and_check


@task(name="Basculer la vue")
def switch_view(config: CloneConfig) -> bool:
    """
    💡 Quoi: basculer la vue 'in_use' vers la nouvelle table
    🎯 Pourquoi: mettre à jour la référence utilisée par l'application
    🏗️ Comment: recréer la vue pour pointer vers la nouvelle table
    """
    log.info(f"Basculement de la vue {config.view_name} vers {config.table_name}")

    clone_view_in_use_switch(
        table_name=config.table_name,
        view_name=config.view_name,
        view_schema_file_path=config.view_schema_file_path,
        dry_run=config.dry_run,
    )
    return True


def clone_view_in_use_switch(
    view_schema_file_path: Path,
    view_name: str,
    table_name: str,
    dry_run: bool,
) -> None:
    """Switching the in-use view to point to the new table"""
    sql = (
        view_schema_file_path.read_text()
        .replace(r"{{view_name}}", view_name)
        .replace(r"{{table_name}}", table_name)
    )
    django_schema_create_and_check(schema_name=table_name, sql=sql, dry_run=dry_run)
