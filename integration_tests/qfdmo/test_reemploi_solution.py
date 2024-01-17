import pytest
from django.conf import settings
from django.core.management import call_command

from qfdmo.models.action import CachedDirectionAction


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "categories",
            "action_directions",
            "actions",
            "acteur_services",
            "acteur_types",
        )
        CachedDirectionAction.reload_cache()


class TestReemploiSolutionView:
    @pytest.mark.django_db
    def test_without_parameters(self, client):
        url = ""

        response = client.get(url)

        assert response.status_code == 200
        assert response.context_data["location"] == "{}"
        assert response.context_data["acteurs"].count() == 0
        assert response.context_data["form"].initial == {
            "sous_categorie_objet": None,
            "sc_id": None,
            "adresse": None,
            "direction": settings.DEFAULT_ACTION_DIRECTION,
            "action_list": None,
            "latitude": None,
            "longitude": None,
            "label_reparacteur": None,
        }
