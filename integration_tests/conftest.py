import pytest
from django.core.management import call_command


@pytest.fixture(scope="session", autouse=True)
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Fixture qui charge les données de test une seule fois pour toute la session
    et les conserve pendant l'exécution de tous les tests
    """
    with django_db_blocker.unblock():
        # Charger les fixtures nécessaires
        call_command("loaddata", "qfdmd/fixtures/produits.json")
        call_command("loaddata", "qfdmo/fixtures/categories.json")
        call_command("loaddata", "qfdmo/fixtures/actions.json")
        call_command("loaddata", "qfdmo/fixtures/acteur_services.json")
        call_command("loaddata", "qfdmo/fixtures/acteur_types.json")
