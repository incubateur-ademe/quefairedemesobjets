import pytest
from django.core.management import call_command

from qfdmo.models import Action, CachedDirectionAction
from unit_tests.qfdmo.acteur_factory import (
    ActeurServiceFactory,
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)


@pytest.fixture(scope="session")
def populate_admin_object(django_db_blocker):
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


@pytest.fixture()
def displayedacteur(db, populate_admin_object):
    action1 = Action.objects.get(nom="reparer")
    action2 = Action.objects.get(nom="echanger")
    action3 = Action.objects.get(nom="louer")
    acteur_service = ActeurServiceFactory.create()
    displayedacteur = DisplayedActeurFactory.create()
    DisplayedPropositionServiceFactory(
        acteur=displayedacteur, acteur_service=acteur_service, action=action1
    )
    DisplayedPropositionServiceFactory(
        acteur=displayedacteur, acteur_service=acteur_service, action=action2
    )
    DisplayedPropositionServiceFactory(
        acteur=displayedacteur, acteur_service=acteur_service, action=action3
    )
    yield displayedacteur


class TestSolutionDetail:
    @pytest.mark.django_db
    def test_solution_detail(self, client, displayedacteur):
        url = f"/solution/{displayedacteur.identifiant_unique}"

        response = client.get(url)

        assert response.status_code == 200
        assert displayedacteur.nom in str(response.content)
