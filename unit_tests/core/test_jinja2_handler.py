import random

import pytest
from django.core.management import call_command
from django.http import HttpRequest

from core.jinja2_handler import action_by_direction, action_list_display, is_iframe


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "action_directions",
            "actions",
        )


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
    @pytest.mark.django_db
    def test_action_list_default(self):
        request = HttpRequest()

        request.GET = {}

        assert action_list_display(request) == [
            "Réparer",
            "Prêter",
            "Donner",
            "Èchanger",
            "Louer",
            "Vendre",
        ]

    @pytest.mark.django_db
    def test_action_list_jai(self):
        request = HttpRequest()

        request.GET = {"direction": "jai"}

        assert action_list_display(request) == [
            "Réparer",
            "Prêter",
            "Donner",
            "Èchanger",
            "Louer",
            "Vendre",
        ]

    @pytest.mark.django_db
    def test_action_list_jecherche(self):
        request = HttpRequest()

        request.GET = {"direction": "jecherche"}

        assert action_list_display(request) == [
            "Emprunter",
            "Èchanger",
            "Louer",
            "Acheter",
        ]

    @pytest.mark.django_db
    def test_action_list_fake(self):
        request = HttpRequest()

        request.GET = {"action_list": "fake"}

        assert action_list_display(request) == []

    @pytest.mark.django_db
    def test_action_list_good(self):
        request = HttpRequest()

        request.GET = {"action_list": "emprunter"}

        assert action_list_display(request) == ["Emprunter"]


class TestActionByDirection:
    @pytest.mark.django_db
    def test_action_by_direction_default(self):
        request = HttpRequest()

        request.GET = {}

        assert [
            action["nom_affiche"] for action in action_by_direction(request, "jai")
        ] == [
            "Réparer",
            "Prêter",
            "Donner",
            "Èchanger",
            "Louer",
            "Vendre",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jai")
            if action["active"]
        ] == [
            "Réparer",
            "Prêter",
            "Donner",
            "Èchanger",
            "Louer",
            "Vendre",
        ]

        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
        ] == [
            "Emprunter",
            "Èchanger",
            "Louer",
            "Acheter",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
            if action["active"]
        ] == [
            "Emprunter",
            "Èchanger",
            "Louer",
            "Acheter",
        ]

    @pytest.mark.django_db
    def test_action_by_direction_jai(self):
        request = HttpRequest()

        request.GET = {"direction": "jecherche", "action_list": "emprunter|louer"}

        assert [
            action["nom_affiche"] for action in action_by_direction(request, "jai")
        ] == [
            "Réparer",
            "Prêter",
            "Donner",
            "Èchanger",
            "Louer",
            "Vendre",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jai")
            if action["active"]
        ] == [
            "Réparer",
            "Prêter",
            "Donner",
            "Èchanger",
            "Louer",
            "Vendre",
        ]

        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
        ] == [
            "Emprunter",
            "Èchanger",
            "Louer",
            "Acheter",
        ]
        assert [
            action["nom_affiche"]
            for action in action_by_direction(request, "jecherche")
            if action["active"]
        ] == [
            "Emprunter",
            "Louer",
        ]
