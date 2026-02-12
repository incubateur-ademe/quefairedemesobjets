import pytest
from django.core.management import call_command
from django.db import connection


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")
        call_command(
            "loaddata",
            "acteur_types",
            "actions",
        )
