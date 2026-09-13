import json

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from core.constants import DIGITAL_ACTEUR_CODE
from qfdmo.models.acteur import NOMBRE_MAX_LIEUX, DisplayedActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

PARIS = {"lat": "48.8534", "lon": "2.3488"}
PARIS_POINT = Point(2.3488, 48.8534, srid=4326)


def get_lieux(client, **params):
    return client.get(reverse("assistant:lieux-geojson"), {**PARIS, **params})


def place_offering(groupe_code, *, at=PARIS_POINT, action_code=None, acteur_type=None):
    groupe = GroupeActionFactory(code=groupe_code)
    action = ActionFactory(code=action_code or groupe_code, groupe_action=groupe)
    acteur = DisplayedActeurFactory(
        location=at, **({"acteur_type": acteur_type} if acteur_type else {})
    )
    DisplayedPropositionServiceFactory(acteur=acteur, action=action)
    return acteur


@pytest.mark.django_db
class TestParametres:
    def test_returns_400_when_geste_missing(self, client):
        assert client.get(reverse("assistant:lieux-geojson"), PARIS).status_code == 400

    def test_returns_400_when_position_missing(self, client):
        response = client.get(reverse("assistant:lieux-geojson"), {"geste": "reparer"})
        assert response.status_code == 400

    def test_returns_400_on_non_numeric_coordinates(self, client):
        assert get_lieux(client, geste="reparer", lat="ici").status_code == 400

    def test_returns_400_on_unreadable_bbox(self, client):
        assert get_lieux(client, geste="reparer", bbox="pas-du-json").status_code == 400

    def test_unreadable_bbox_does_not_fall_back_to_coordinates(self, client):
        """Un repli masquerait un bug client et afficherait une autre zone."""
        assert get_lieux(client, geste="reparer", bbox="{}").status_code == 400


@pytest.mark.django_db
class TestReponse:
    def test_serves_a_feature_collection(self, client):
        place_offering("reparer")
        payload = json.loads(get_lieux(client, geste="reparer").content)
        assert payload["type"] == "FeatureCollection"
        assert len(payload["features"]) == 1

    def test_caps_results_at_twenty_places(self, client):
        groupe = GroupeActionFactory(code="reparer")
        action = ActionFactory(code="reparer", groupe_action=groupe)
        for _ in range(NOMBRE_MAX_LIEUX + 5):
            acteur = DisplayedActeurFactory(location=PARIS_POINT)
            DisplayedPropositionServiceFactory(acteur=acteur, action=action)

        payload = json.loads(get_lieux(client, geste="reparer").content)
        assert len(payload["features"]) == NOMBRE_MAX_LIEUX

    def test_deduplicates_acteur_offering_several_actions_of_a_geste(self, client):
        """« Donner » couvre donner, échanger et rapporter : un lieu, une fois."""
        groupe = GroupeActionFactory(code="donner_echanger_rapporter")
        acteur = DisplayedActeurFactory(location=PARIS_POINT)
        for code in ("donner", "echanger", "rapporter"):
            DisplayedPropositionServiceFactory(
                acteur=acteur,
                action=ActionFactory(code=code, groupe_action=groupe),
            )

        payload = json.loads(
            get_lieux(client, geste="donner_echanger_rapporter").content
        )
        assert len(payload["features"]) == 1

    def test_ignores_places_offering_another_geste(self, client):
        place_offering("trier")
        payload = json.loads(get_lieux(client, geste="reparer").content)
        assert payload["features"] == []

    def test_orders_by_proximity(self, client):
        groupe = GroupeActionFactory(code="reparer")
        action = ActionFactory(code="reparer", groupe_action=groupe)
        for longitude in (2.60, 2.40, 2.35):
            acteur = DisplayedActeurFactory(
                location=Point(longitude, 48.8534, srid=4326)
            )
            DisplayedPropositionServiceFactory(acteur=acteur, action=action)

        lieux = json.loads(get_lieux(client, geste="reparer").content)["features"]
        longitudes = [feature["geometry"]["coordinates"][0] for feature in lieux]
        assert longitudes == [2.35, 2.40, 2.60]

    def test_exposes_only_what_the_map_needs(self, client):
        place_offering("reparer")
        payload = json.loads(get_lieux(client, geste="reparer").content)
        assert set(payload["features"][0]["properties"]) == {"uuid", "nom", "bonus"}

    def test_excludes_digital_acteurs(self, client):
        place_offering(
            "reparer", acteur_type=ActeurTypeFactory(code=DIGITAL_ACTEUR_CODE)
        )
        payload = json.loads(get_lieux(client, geste="reparer").content)
        assert payload["features"] == []

    def test_is_cacheable(self, client):
        place_offering("reparer")
        response = get_lieux(client, geste="reparer")
        assert "max-age" in response.headers["Cache-Control"]


@pytest.mark.django_db
class TestRequetes:
    def test_answers_in_a_single_query(self, client, django_assert_num_queries):
        place_offering("reparer")
        with django_assert_num_queries(1):
            get_lieux(client, geste="reparer")

    def test_within_uses_the_indexed_bounding_box_operator(self):
        """`within` sur une colonne geography ignore l'index et coûte 2 s."""
        sql = str(
            DisplayedActeur.objects.all()
            .proposing("reparer")
            .within([2.30, 48.83, 2.40, 48.88])
            .for_the_map()
            .query
        )
        assert "&&" in sql
        assert "ST_Within" not in sql

    def test_nearest_to_does_not_bound_the_search(self):
        """Une borne de distance empêcherait le parcours ordonné de l'index."""
        sql = str(
            DisplayedActeur.objects.all()
            .proposing("reparer")
            .nearest_to(2.3488, 48.8534)
            .for_the_map()
            .query
        )
        assert "ST_DWithin" not in sql
        assert "<->" in sql
