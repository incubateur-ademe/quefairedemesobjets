from django.contrib.gis.geos import Point
import pytest
from django.http import HttpRequest

from qfdmo.models.acteur import ActeurStatus
from qfdmo.views.adresses import AddressesView
from unit_tests.core.test_utils import query_dict_from
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


class TestAdessesViewGetActionList:
    @pytest.mark.parametrize(
        "params,action_list",
        [
            (
                {},
                [
                    "prêter",
                    "mettre en location",
                    "réparer",
                    "donner",
                    "échanger",
                    "vendre",
                ],
            ),
            (
                {"direction": "fake"},
                [
                    "prêter",
                    "mettre en location",
                    "réparer",
                    "donner",
                    "échanger",
                    "vendre",
                ],
            ),
            (
                {"direction": "jai"},
                [
                    "prêter",
                    "mettre en location",
                    "réparer",
                    "donner",
                    "échanger",
                    "vendre",
                ],
            ),
            (
                {"direction": "jecherche"},
                ["emprunter", "louer", "échanger", "acheter de seconde main"],
            ),
            ({"action_list": "fake"}, []),
            ({"action_list": "preter"}, ["prêter"]),
            ({"action_list": "preter|reparer"}, ["prêter", "réparer"]),
        ],
    )
    @pytest.mark.django_db
    def test_get_action_list(self, params, action_list):
        request = HttpRequest()
        request.GET = params
        adresses_view = AddressesView()
        adresses_view.request = request

        assert [
            action["libelle"] for action in adresses_view.get_action_list()
        ] == action_list


@pytest.fixture
def action_reparer():
    action = ActionFactory(code="reparer")
    return action


@pytest.fixture
def action_preter():
    action = ActionFactory(code="preter")
    return action


@pytest.fixture
def sous_categorie():
    sous_categorie = SousCategorieObjetFactory()
    return sous_categorie


@pytest.fixture
def proposition_service(action_reparer, sous_categorie):
    proposition_service = DisplayedPropositionServiceFactory(
        action=action_reparer,
    )
    proposition_service.sous_categories.add(sous_categorie)
    return proposition_service


@pytest.fixture
def adresses_view(proposition_service):
    reparacteur = LabelQualiteFactory(code="reparacteur")

    displayed_acteur = DisplayedActeurFactory(
        exclusivite_de_reprisereparation=True,
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )
    displayed_acteur.labels.add(reparacteur)
    displayed_acteur.proposition_services.add(proposition_service)

    adresses_view = AddressesView()
    return adresses_view


@pytest.mark.django_db
class TestExclusiviteReparation:
    def test_pas_action_reparer_exclut_acteurs_avec_exclusivite(
        self, adresses_view, action_preter
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_preter.code],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["true"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 0

    def test_action_reparer_exclut_par_defaut_acteurs_avec_exclusivite(
        self, adresses_view, action_reparer, action_preter
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [f"{action_reparer.code}|{action_preter.code}"],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["true"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 0

    def test_action_reparer_et_exclusivite_inclut_acteurs_avec_exclusivite(
        self, adresses_view, action_reparer
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_reparer.code],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["false"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 1

    def test_sous_categorie_filter_works_with_exclu_reparation(
        self, adresses_view, sous_categorie, action_reparer
    ):
        request = HttpRequest()
        sous_categorie_id = sous_categorie.id
        request.GET = query_dict_from(
            {
                "action_list": [action_reparer.code],
                "latitude": [1],
                "longitude": [1],
                "sc_id": [str(sous_categorie_id)],
                "pas_exclusivite_reparation": ["false"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 1

    def test_action_filter_works_with_exclu_reparation(
        self, adresses_view, action_reparer, action_preter, sous_categorie
    ):
        action_donner = ActionFactory(code="donner")

        proposition_service_preter = DisplayedPropositionServiceFactory(
            action=action_preter,
        )
        proposition_service_donner = DisplayedPropositionServiceFactory(
            action=action_donner,
        )

        proposition_service_preter.sous_categories.add(sous_categorie)
        proposition_service_donner.sous_categories.add(sous_categorie)

        displayed_acteur_preter = DisplayedActeurFactory(
            nom="Un acteur preter",
            location=Point(1, 1),
            statut=ActeurStatus.ACTIF,
        )
        displayed_acteur_donner = DisplayedActeurFactory(
            nom="Un acteur donner",
            location=Point(1, 1),
            statut=ActeurStatus.ACTIF,
        )

        displayed_acteur_preter.proposition_services.add(proposition_service_preter)
        displayed_acteur_donner.proposition_services.add(proposition_service_donner)

        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [f"{action_reparer.code}|{action_preter.code}"],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["false"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 2
