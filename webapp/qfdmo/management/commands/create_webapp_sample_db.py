"""
Django command to create the webapp_sample database locally
using the SQL script create_webapp_sample_db.sql
"""

import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections

logger = logging.getLogger(__name__)


def execute_sql_script(conn, file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"Le fichier SQL n'existe pas : {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_script = f.read()
    with conn.cursor() as cursor:
        cursor.execute(sql_script)


class Command(BaseCommand):
    help = """
    Crée la base de données webapp_sample localement en utilisant le script SQL
    init_webapp_sample.sql
    """

    def handle(self, *args, **options):
        connections.close_all()
        conn = connections["default"]

        # Always start from a clean database to avoid leftover state
        # (e.g. partial migrations) from previous runs. Terminate other
        # backends first since DROP DATABASE fails while connections are open.
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'webapp_sample' AND pid <> pg_backend_pid();"
            )
            cursor.execute("DROP DATABASE IF EXISTS webapp_sample;")
            cursor.execute("CREATE DATABASE webapp_sample;")

        # Create user and permissions if it doesn't exist
        repo_root = Path(settings.BASE_DIR).parent
        file_path = repo_root / "scripts" / "sql" / "create_webapp_sample_db.sql"
        execute_sql_script(conn, file_path)

        # Create extensions, then the wagtail_french text search config
        # (kept in its own script so the migration runs the exact same SQL).
        conn = connections["webapp_sample"]
        execute_sql_script(
            conn, repo_root / "scripts" / "sql" / "create_extensions.sql"
        )
        execute_sql_script(
            conn,
            Path(settings.BASE_DIR)
            / "qfdmd"
            / "migrations"
            / "sql"
            / "create_wagtail_french_config.sql",
        )
