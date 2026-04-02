import pytest
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("enable_unaccent")
        call_command("enable_trigram")
        call_command(
            "loaddata",
            "acteur_types",
            "actions",
        )
