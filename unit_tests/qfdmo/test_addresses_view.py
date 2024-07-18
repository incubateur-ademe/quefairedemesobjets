from django.contrib.gis.geos import Point
import pytest
from django.http import HttpRequest

from qfdmo.views.adresses import AddressesView
from unit_tests.core.test_utils import query_dict_from
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory


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
def adresses_view():
    DisplayedActeurFactory(
        exclusivite_de_reprisereparation=True,
        location=Point(1, 1),
    )
    adresses_view = AddressesView()
    return adresses_view


@pytest.mark.django_db
class TestExclusiviteReparation:
    def test_pas_action_reparer_exclut_acteurs_avec_exclusivite(self, adresses_view):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": ["preter"],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["true"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 0

    def test_action_reparer_exclut_par_defaut_acteurs_avec_exclusivite(
        self, adresses_view
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": ["preter|reparer"],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["true"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 0

    def test_action_reparer_et_exclusivite_inclut_acteurs_avec_exclusivite(
        self, adresses_view
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": ["preter|reparer"],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["false"],
            }
        )
        adresses_view.request = request
        context = adresses_view.get_context_data()

        # TODO: comprendre pourquoi c'est pas bon ici...
        # je pense que ca vient du else ligne 413 de views/adresses.py
        assert context["acteurs"].count() == 1
