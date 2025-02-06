import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.http import HttpRequest

from core.jinja2_handler import action_by_direction, distance_to_acteur
from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory, DisplayedActeurFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "actions",
            "acteur_types",
        )


class TestActionByDirection:
    @pytest.mark.django_db
    def test_action_by_direction_default(self):
        request = HttpRequest()

        request.GET = {}

        assert [
            action["libelle"] for action in action_by_direction(request, "jai")
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]
        assert [
            action["libelle"]
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
            action["libelle"] for action in action_by_direction(request, "jecherche")
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]
        assert [
            action["libelle"]
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
            action["libelle"] for action in action_by_direction(request, "jai")
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]
        assert [
            action["libelle"]
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
            action["libelle"] for action in action_by_direction(request, "jecherche")
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]
        assert [
            action["libelle"]
            for action in action_by_direction(request, "jecherche")
            if action["active"]
        ] == [
            "emprunter",
            "louer",
        ]


@pytest.fixture
def adresse():
    return DisplayedActeurFactory(
        adresse="1 rue de la paix",
        location=Point(0, 0),
    )


@pytest.mark.django_db
class TestDistanceToActeur:

    @pytest.mark.parametrize(
        "request_params,expected",
        [
            ({"longitude": "0", "latitude": "0"}, "(0 m)"),
            ({"longitude": str(954 / 111320), "latitude": "0"}, "(950 m)"),
            ({"longitude": "0", "latitude": str(-954 / 111320)}, "(950 m)"),
            ({"longitude": str(955 / 111320), "latitude": "0"}, "(960 m)"),
            ({"longitude": str(1049 / 111320), "latitude": "0"}, "(1,0 km)"),
            ({"longitude": str(1051 / 111320), "latitude": "0"}, "(1,1 km)"),
            (
                {"longitude": str(1000 / 111320), "latitude": str(1000 / 111320)},
                "(1,4 km)",
            ),
            ({"longitude": str(99999 / 111320), "latitude": "0"}, "(100,0 km)"),
        ],
    )
    def test_distance_to_acteur_not_digital(self, adresse, request_params, expected):
        request = type("", (), {})()  # create a dummy object
        request.GET = request_params
        assert distance_to_acteur(request, adresse) == expected

    def test_distance_to_acteur_digital(self, adresse):
        adresse.acteur_type = ActeurTypeFactory(code="acteur_digital")
        request = type("", (), {})()
        request.GET = {"longitude": str(1000 / 111320), "latitude": str(1000 / 111320)}
        assert distance_to_acteur(request, adresse) == ""
