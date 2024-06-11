import random

import pytest
from django.core.management import call_command
from django.http import HttpRequest

from core.jinja2_handler import (
    action_by_direction,
    display_infos_panel,
    display_labels_panel,
    display_sources_panel,
    distance_to_acteur,
    is_embedded,
)
from qfdmo.models import CachedDirectionAction
from qfdmo.models.acteur import ActeurType
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory, LabelQualiteFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "actions",
            "acteur_types",
        )
        CachedDirectionAction.reload_cache()


class TestIsIframe:
    def test_is_embedded_false(self):
        request = HttpRequest()

        request.GET = {}
        assert is_embedded(request) is False

    def test_is_embedded_true(self):
        request = HttpRequest()

        request.GET = {"iframe": str(random.randint(0, 10))}

        assert is_embedded(request) is True

        request.GET = {"iframe": "anything"}

        assert is_embedded(request) is True


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
    )


@pytest.mark.django_db
class TestDisplayInfosPanel:

    def test_display_infos_panel_adresse_not_digital(self, adresse):
        adresse.horaires_description = None
        adresse.adresse = "something"
        assert display_infos_panel(adresse)

        adresse.adresse = None
        assert not display_infos_panel(adresse)

    def test_display_infos_panel_horaires_not_digital(self, adresse):
        adresse.horaires_description = "something"
        adresse.adresse = None
        assert display_infos_panel(adresse)

        adresse.horaires_description = None
        assert not display_infos_panel(adresse)

    def test_display_infos_panel_digital(self, adresse):
        adresse.acteur_type_id = ActeurType.get_digital_acteur_type_id()
        assert not display_infos_panel(adresse)

        adresse.adresse = None
        assert not display_infos_panel(adresse)


@pytest.mark.django_db
class TestDisplayLabelsPanel:

    def test_display_labels_panel(self, adresse):
        assert not display_labels_panel(adresse)
        label = LabelQualiteFactory(
            afficher=True,
            type_enseigne=False,
        )
        adresse.labels.add(label)
        assert display_labels_panel(adresse)
        label.afficher = False
        label.save()
        assert not display_labels_panel(adresse)
        label.afficher = True
        label.type_enseigne = True
        label.save()
        assert not display_labels_panel(adresse)


@pytest.mark.django_db
class TestDisplaySourcesPanel:

    def test_display_sources_panel(self, adresse):
        assert display_sources_panel(adresse)
        adresse.source.afficher = False
        assert not display_sources_panel(adresse)


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
        adresse.acteur_type_id = ActeurType.get_digital_acteur_type_id()
        request = type("", (), {})()
        request.GET = {"longitude": str(1000 / 111320), "latitude": str(1000 / 111320)}
        assert distance_to_acteur(request, adresse) == ""
