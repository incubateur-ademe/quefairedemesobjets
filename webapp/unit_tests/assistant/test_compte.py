import json

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

pytestmark = pytest.mark.django_db

ANGERS = {"longitude": "-0.5616", "latitude": "47.4675"}


def place_offering(action, longitude, latitude):
    acteur = DisplayedActeurFactory(location=Point(longitude, latitude, srid=4326))
    DisplayedPropositionServiceFactory(acteur=acteur, action=action)
    return acteur


@pytest.fixture
def reparer():
    groupe = GroupeActionFactory(code="reparer")
    return ActionFactory(code="reparer", groupe_action=groupe)


def get_count(client, **params):
    return client.get(reverse("assistant:solutions-compte"), {**ANGERS, **params})


class TestSolutionsCount:
    def test_counts_the_places_within_twenty_kilometres(self, client, reparer):
        place_offering(reparer, -0.55, 47.47)  # in town
        place_offering(reparer, -0.40, 47.40)  # ~14 km away
        place_offering(reparer, 2.35, 48.85)  # Paris

        payload = json.loads(get_count(client, geste="reparer").content)

        assert payload == {"count": 2}

    def test_counts_the_union_of_a_block_with_two_gestes(self, client, reparer):
        donner = GroupeActionFactory(code="donner_echanger_rapporter")
        place_offering(reparer, -0.55, 47.47)
        place_offering(ActionFactory(code="donner", groupe_action=donner), -0.56, 47.46)

        payload = json.loads(
            get_count(client, geste=["reparer", "donner_echanger_rapporter"]).content
        )

        assert payload == {"count": 2}

    def test_returns_400_without_position(self, client, reparer):
        response = client.get(
            reverse("assistant:solutions-compte"), {"geste": "reparer"}
        )
        assert response.status_code == 400

    def test_returns_400_without_geste(self, client):
        assert get_count(client).status_code == 400

    def test_returns_400_on_unknown_objet(self, client, reparer):
        assert get_count(client, geste="reparer", fiche="inconnu").status_code == 400

    def test_is_cacheable(self, client, reparer):
        assert "max-age" in get_count(client, geste="reparer").headers["Cache-Control"]
