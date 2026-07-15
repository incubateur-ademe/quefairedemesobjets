from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0190_alter_carteconfig_supprimer_branding"),
    ]

    db_port = (
        5432
        if settings.DATABASES["default"]["HOST"] == "localhost"
        else settings.DATABASES["default"]["PORT"]
    )

    operations = [
        migrations.RunSQL(
            f"""
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
            CREATE SCHEMA IF NOT EXISTS webapp_public;
            IMPORT FOREIGN SCHEMA public FROM SERVER qfdmo_server INTO webapp_public;
            """,
            """
            DROP SERVER IF EXISTS qfdmo_server CASCADE;
            """,
        ),
    ]
