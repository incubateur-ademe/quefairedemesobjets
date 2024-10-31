import pytest
from django.http import HttpRequest

from qfdmo.views.adresses import CarteView
from unit_tests.core.test_utils import query_dict_from


@pytest.mark.django_db
class TestAdresseViewMixins:
    def test_iframe_mixin_is_carte(self):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "carte": "coucou",
            }
        )
        adresses_view = CarteView()
        adresses_view.setup(request)
        assert adresses_view.is_carte
        assert adresses_view.get_context_data()["is_carte"]
        assert adresses_view.is_embedded
        assert adresses_view.get_context_data()["is_embedded"]

    def test_iframe_mixin_is_iframe(self):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "iframe": "coucou",
            }
        )
        adresses_view = CarteView()
        adresses_view.setup(request)
        assert adresses_view.is_iframe
        assert adresses_view.get_context_data()["is_iframe"]
        assert adresses_view.is_embedded
        assert adresses_view.get_context_data()["is_embedded"]

    def test_digital_mixin(self):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "digital": "1",
            }
        )
        adresses_view = CarteView()
        adresses_view.setup(request)
        assert adresses_view.get_context_data()["is_digital"]


class TestAdressesViewGetActionList:
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
        adresses_view = CarteView()
        adresses_view.setup(request)

        assert [
            action["libelle"] for action in adresses_view.get_action_list()
        ] == action_list
