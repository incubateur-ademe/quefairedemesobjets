from django.conf import settings
from django.db import connections
from django.utils.encoding import force_str
from django.utils.functional import Promise
from wagtail.fields import DjangoJSONEncoder

from qfdmo.models.action import get_directions


def get_direction(request, is_carte=False):
    default_direction = None if is_carte else settings.DEFAULT_ACTION_DIRECTION
    direction = request.GET.get("direction", default_direction)
    if direction not in [d["code"] for d in get_directions()]:
        direction = default_direction
    return direction


class LazyEncoder(DjangoJSONEncoder):
    """
    Force lazy strings to text

    Inspired by https://github.com/hiimdoublej/django-json-ld/blob/master/django_json_ld/util.py
    """

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        return super(LazyEncoder, self).default(obj)


SQL_CREATE_EXTENSIONS = """
                CREATE EXTENSION IF NOT EXISTS postgis;
                CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
                CREATE EXTENSION IF NOT EXISTS unaccent;
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE EXTENSION IF NOT EXISTS postgres_fdw;
                """


def _create_schema_public_in_db(
    current_db_connection_name,
    remote_server_name,
    remote_schema_name,
    db_host,
    db_port,
    db_name,
    db_user,
    db_password,
):
    with connections[current_db_connection_name].cursor() as cursor:
        cursor.execute(SQL_CREATE_EXTENSIONS)
        sql_create_server_connection = f"""
                DROP SERVER IF EXISTS {remote_server_name} CASCADE;
        """
        sql_create_server_connection += f"""
        CREATE SERVER {remote_server_name} FOREIGN DATA WRAPPER postgres_fdw
          OPTIONS (
            host '{db_host}',
            port '{db_port}',
            dbname '{db_name}'
          );
        """
        sql_create_server_connection += f"""
        CREATE USER MAPPING FOR CURRENT_USER SERVER {remote_server_name}
          OPTIONS (
            user '{db_user}',
            password '{db_password}'
          );
        """
        sql_create_server_connection += f"""
        CREATE SCHEMA IF NOT EXISTS {remote_schema_name};
        """
        sql_create_server_connection += f"""
        IMPORT FOREIGN SCHEMA public FROM SERVER {remote_server_name}
        INTO {remote_schema_name};
        """
        cursor.execute(sql_create_server_connection)

    return sql_create_server_connection


def create_schema_webapp_public_in_warehouse_db():
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

    return _create_schema_public_in_db(
        current_db_connection_name="warehouse",
        remote_server_name="webapp_server",
        remote_schema_name="webapp_public",
        db_host=db_host,
        db_port=db_port,
        db_name=settings.DATABASES["default"]["NAME"],
        db_user=settings.DATABASES["default"]["USER"],
        db_password=settings.DATABASES["default"]["PASSWORD"],
    )


def create_schema_warehouse_public_in_webapp_db():
    db_port = (
        5432
        if settings.ENVIRONMENT == "development"
        else settings.DATABASES["warehouse"]["PORT"]
    )
    db_host = (
        "lvao-warehouse-db"
        if settings.ENVIRONMENT == "development"
        else settings.DATABASES["warehouse"]["HOST"]
    )

    return _create_schema_public_in_db(
        current_db_connection_name="default",
        remote_server_name="warehouse_server",
        remote_schema_name="warehouse_public",
        db_host=db_host,
        db_port=db_port,
        db_name=settings.DATABASES["warehouse"]["NAME"],
        db_user=settings.DATABASES["warehouse"]["USER"],
        db_password=settings.DATABASES["warehouse"]["PASSWORD"],
    )
