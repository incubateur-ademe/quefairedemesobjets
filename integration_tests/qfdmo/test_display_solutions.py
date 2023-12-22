import pytest
from django.core.management import call_command

from qfdmo.models import Action, CachedDirectionAction, FinalActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurServiceFactory,
    PropositionServiceFactory,
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
def finalacteur(db, populate_admin_object):
    action1 = Action.objects.get(nom="reparer")
    action2 = Action.objects.get(nom="echanger")
    action3 = Action.objects.get(nom="louer")
    acteur_service = ActeurServiceFactory.create()
    acteur = ActeurFactory.create()
    PropositionServiceFactory(
        acteur=acteur, acteur_service=acteur_service, action=action1
    )
    PropositionServiceFactory(
        acteur=acteur, acteur_service=acteur_service, action=action2
    )
    PropositionServiceFactory(
        acteur=acteur, acteur_service=acteur_service, action=action3
    )
    FinalActeur.refresh_view()
    yield FinalActeur.objects.get(identifiant_unique=acteur.identifiant_unique)


class TestSolutionDetail:
    @pytest.mark.django_db
    def test_solution_detail(self, client, finalacteur):
        url = f"/solution/{finalacteur.identifiant_unique}"

        response = client.get(url)

        assert response.status_code == 200
        assert finalacteur.nom in str(response.content)
