from pathlib import Path

from utils.django import django_schema_create_and_check


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
