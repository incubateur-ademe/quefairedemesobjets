from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    def handle(self, *args, **options):
        db_port = (
            5432
            if settings.ENVIRONMENT == "development"
            else settings.DATABASES["default"]["PORT"]
        )

        with connection.cursor() as cursor:
            # flake8: noqa: E501
            sql = f"""
                CREATE EXTENSION IF NOT EXISTS postgis;
                CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
                CREATE EXTENSION IF NOT EXISTS unaccent;
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE EXTENSION IF NOT EXISTS postgres_fdw;
                DROP SERVER IF EXISTS qfdmo_server CASCADE;
                CREATE EXTENSION IF NOT EXISTS postgres_fdw;
                CREATE SERVER qfdmo_server FOREIGN DATA WRAPPER postgres_fdw
                  OPTIONS (
                    host '{settings.DATABASES["default"]["HOST"]}',
                    port '{db_port}',
                    dbname '{settings.DATABASES["default"]["NAME"]}'
                  );
                CREATE USER MAPPING FOR CURRENT_USER SERVER qfdmo_server
                  OPTIONS (
                    user '{settings.DATABASES["default"]["USER"]}',
                    password '{settings.DATABASES["default"]["PASSWORD"]}'
                  );
                CREATE SCHEMA IF NOT EXISTS foreign_qfdmo_public;
                IMPORT FOREIGN SCHEMA public FROM SERVER qfdmo_server INTO foreign_qfdmo_public;
                DROP SERVER IF EXISTS qfdmo_server CASCADE;
                """
            cursor.execute(sql)
