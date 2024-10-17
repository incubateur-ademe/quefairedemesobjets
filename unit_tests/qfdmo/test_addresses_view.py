import pytest
from django.http import HttpRequest

from qfdmo.views.adresses import AddressesView


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
        adresses_view.setup(request)

        assert [
            action["libelle"] for action in adresses_view.get_action_list()
        ] == action_list
