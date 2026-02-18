from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import connections
from django.utils.encoding import force_str
from django.utils.functional import Promise
from wagtail.fields import DjangoJSONEncoder

SQL_CREATE_EXTENSIONS = """
                CREATE EXTENSION IF NOT EXISTS postgis;
                CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
                CREATE EXTENSION IF NOT EXISTS unaccent;
                CREATE EXTENSION IF NOT EXISTS pg_trgm;
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE EXTENSION IF NOT EXISTS postgres_fdw;
                """


class LazyEncoder(DjangoJSONEncoder):
    """
    Force lazy strings to text

    Inspired by https://github.com/hiimdoublej/django-json-ld/blob/master/django_json_ld/util.py
    """

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        return super(LazyEncoder, self).default(obj)


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

    return _create_schema_public_in_db(
        current_db_connection_name="warehouse",
        remote_server_name=settings.REMOTE_WEBAPP_SERVERNAME,
        remote_schema_name=settings.REMOTE_WEBAPP_SCHEMANAME,
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
        remote_server_name=settings.REMOTE_WAREHOUSE_SERVERNAME,
        remote_schema_name=settings.REMOTE_WAREHOUSE_SCHEMANAME,
        db_host=db_host,
        db_port=db_port,
        db_name=settings.DATABASES["warehouse"]["NAME"],
        db_user=settings.DATABASES["warehouse"]["USER"],
        db_password=settings.DATABASES["warehouse"]["PASSWORD"],
    )


def has_explicit_perm(user, perm_str):
    """
    use in place of has_perm, avoid to return always true for superadmin
    https://docs.djangoproject.com/en/5.2/ref/contrib/auth/#django.contrib.auth.models.User.has_perm
    """
    app_label, codename = perm_str.split(".")
    try:
        perm = Permission.objects.get(
            codename=codename, content_type__app_label=app_label
        )
    except Permission.DoesNotExist:
        return False

    if perm in user.user_permissions.all():
        return True

    for group in user.groups.all():
        if perm in group.permissions.all():
            return True

    return False


def remove_protocol_from_url(url):
    """
    Convert an absolute URL to a protocol-relative URL.
    This prevents mixed content issues in Django Lookbook previews
    where the iframe may use http:// but BASE_URL is https://.

    Example:
        https://example.com/path -> //example.com/path
        http://example.com/path -> //example.com/path
    """
    parsed = urlparse(url)
    return f"//{parsed.netloc}{parsed.path}"
