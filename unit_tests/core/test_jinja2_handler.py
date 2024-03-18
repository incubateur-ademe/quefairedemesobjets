import random

import pytest
from django.core.management import call_command
from django.http import HttpRequest

from core.jinja2_handler import action_by_direction, action_list_display, is_iframe
from qfdmo.models import CachedDirectionAction


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "action_directions",
            "actions",
        )
        CachedDirectionAction.reload_cache()


class TestIsIframe:
    def test_is_iframe_false(self):
        request = HttpRequest()

        request.GET = {}
        assert is_iframe(request) is False

    def test_is_iframe_true(self):
        request = HttpRequest()

        request.GET = {"iframe": str(random.randint(0, 10))}

        assert is_iframe(request) is True

        request.GET = {"iframe": "anything"}

        assert is_iframe(request) is True


class TestActionDisplayList:

    @pytest.mark.parametrize(
        "params,action_list",
        [
            (
                {},
                ["emprunter", "louer", "échanger", "acheter de seconde main"],
            ),
            (
                {"direction": "fake"},
                ["emprunter", "louer", "échanger", "acheter de seconde main"],
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
            ({"action_list": "emprunter"}, ["emprunter"]),
            ({"action_list": "emprunter|louer"}, ["emprunter", "louer"]),
        ],
    )
    @pytest.mark.django_db
    def test_action_list(self, params, action_list):
        request = HttpRequest()

        request.GET = params

        assert action_list_display(request) == action_list


class TestActionByDirection:
    @pytest.mark.django_db
    def test_action_by_direction_default(self):
        request = HttpRequest()

        request.GET = {}

        assert [
            action["nom_affiche"] for action in action_by_direction(request, "jai")
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jai")
            if action["active"]
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]

        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
            if action["active"]
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]

    @pytest.mark.django_db
    def test_action_by_direction_jai(self):
        request = HttpRequest()

        request.GET = {"direction": "jecherche", "action_list": "emprunter|louer"}

        assert [
            action["nom_affiche"] for action in action_by_direction(request, "jai")
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jai")
            if action["active"]
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]

        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
            if action["active"]
        ] == [
            "emprunter",
            "louer",
        ]
