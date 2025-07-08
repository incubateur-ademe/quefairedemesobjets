from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    def handle(self, *args, **options):
        with connections["warehouse"].cursor() as cursor:
            # flake8: noqa: E501
            sql = f"""
                CREATE EXTENSION IF NOT EXISTS postgis;
                CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
                CREATE EXTENSION IF NOT EXISTS unaccent;
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE EXTENSION IF NOT EXISTS postgres_fdw;
                DROP SERVER IF EXISTS qfdmo_server CASCADE;
                CREATE SERVER qfdmo_server FOREIGN DATA WRAPPER postgres_fdw
                  OPTIONS (
                    host 'localhost',
                    port '5432',
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
