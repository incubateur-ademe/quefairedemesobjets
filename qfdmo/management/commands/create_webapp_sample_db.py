"""
Django command to create the webapp_sample database locally
using the SQL script create_webapp_sample_db.sql
"""

import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import ProgrammingError, connections

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
        conn = connections["default"]

        # Create database if it doesn't exist
        try:
            conn.cursor().execute("CREATE DATABASE webapp_sample;")
        except ProgrammingError:
            logger.warning("La base de données webapp_sample existe déjà")

        # Create user and permissions if it doesn't exist
        file_path = (
            Path(settings.BASE_DIR) / "scripts" / "sql" / "create_webapp_sample_db.sql"
        )
        execute_sql_script(conn, file_path)

        # Create extensions
        conn = connections["webapp_sample"]
        file_path = (
            Path(settings.BASE_DIR) / "scripts" / "sql" / "create_extensions.sql"
        )
        execute_sql_script(conn, file_path)
