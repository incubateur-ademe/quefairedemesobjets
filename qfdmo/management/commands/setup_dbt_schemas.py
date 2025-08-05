from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Setup postgres schemas required by dbt"""
        # This command usually runs locally, where postgres runs in Docker.
        # Locally, the postgres port set for Django is different than the
        # one exposed by the container as we expose the 5432 port on 6543
        # port on the machine.
        # As the django server does not run in docker, we cannot use the same port
        # as the postgres server uses 5432 port internally.
        #
        # This logic could be removed if the django server was running in docker, but
        # this is not planned at the moment.
        db_port = (
            5432
            if settings.ENVIRONMENT == "development"
            else settings.DATABASES["default"]["PORT"]
        )
        db_host = (
            "lvao-webapp-db"
            if settings.ENVIRONMENT == "development"
            else settings.DATABASES["default"]["HOST"]
        )

        with connections["warehouse"].cursor() as cursor:
            # flake8: noqa: E501
            sql_create_extensions = """
                CREATE EXTENSION IF NOT EXISTS postgis;
                CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
                CREATE EXTENSION IF NOT EXISTS unaccent;
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE EXTENSION IF NOT EXISTS postgres_fdw;
                """
            sql_create_server_connection = f"""
                DROP SERVER IF EXISTS qfdmo_server CASCADE;
                CREATE SERVER qfdmo_server FOREIGN DATA WRAPPER postgres_fdw
                  OPTIONS (
                    host '{db_host}',
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
                """

            self.stdout.write(self.style.NOTICE(sql_create_extensions))
            cursor.execute(sql_create_extensions)

            self.stdout.write(self.style.NOTICE(sql_create_server_connection))
            cursor.execute(sql_create_server_connection)
