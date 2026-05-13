"""Tests for the GeoJSON acteurs endpoint that feeds the auto-search-on-pan
feature on the carte. Covers happy path, exclude_uuids, filters, and validation."""

import json

import pytest
from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from qfdmo.models import GroupeAction
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)


def _url() -> str:
    return reverse("qfdmo:carte_acteurs_geojson")


def _bbox_around(lng: float, lat: float, half: float = 0.05) -> str:
    return f"{lng - half},{lat - half},{lng + half},{lat + half}"


@pytest.mark.django_db
class TestCarteActeursGeojson:
    @pytest.fixture
    def client(self) -> Client:
        return Client()

    @pytest.fixture
    def reparer_action(self):
        return GroupeAction.objects.get(code="reparer").actions.first()

    def test_returns_400_when_bbox_missing(self, client):
        response = client.get(_url())
        assert response.status_code == 400

    def test_returns_400_when_bbox_invalid(self, client):
        response = client.get(_url(), {"bbox": "not,a,valid,bbox"})
        assert response.status_code == 400

    def test_returns_features_in_bbox(self, client, reparer_action):
        # In-bbox acteur: Auray-ish.
        in_bbox = DisplayedActeurFactory(location=Point(-2.99, 47.66))
        DisplayedPropositionServiceFactory(action=reparer_action, acteur=in_bbox)

        # Out-of-bbox acteur (Paris).
        out_of_bbox = DisplayedActeurFactory(location=Point(2.35, 48.85))
        DisplayedPropositionServiceFactory(action=reparer_action, acteur=out_of_bbox)

        response = client.get(_url(), {"bbox": _bbox_around(-2.99, 47.66)})
        assert response.status_code == 200
        payload = json.loads(response.content)

        uuids = {f["properties"]["uuid"] for f in payload["features"]}
        assert str(in_bbox.uuid) in uuids
        assert str(out_of_bbox.uuid) not in uuids

    def test_geojson_shape(self, client, reparer_action):
        acteur = DisplayedActeurFactory(location=Point(-2.99, 47.66))
        DisplayedPropositionServiceFactory(action=reparer_action, acteur=acteur)

        response = client.get(_url(), {"bbox": _bbox_around(-2.99, 47.66)})
        payload = json.loads(response.content)

        assert payload["type"] == "FeatureCollection"
        feature = next(
            f for f in payload["features"] if f["properties"]["uuid"] == str(acteur.uuid)
        )
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        # GeoJSON: coordinates are [lng, lat].
        assert feature["geometry"]["coordinates"] == pytest.approx([-2.99, 47.66])
        # Icon name mirrors `iconNameFor` in static/to_compile/js/acteur_icons.ts.
        assert feature["properties"]["icon"].startswith("acteur:")
        assert feature["properties"]["bonus"] is False
        assert feature["properties"]["detail_url"].endswith(str(acteur.uuid))

    def test_exclude_uuids_filters_out_listed_acteurs(self, client, reparer_action):
        keep = DisplayedActeurFactory(location=Point(-2.99, 47.66))
        DisplayedPropositionServiceFactory(action=reparer_action, acteur=keep)
        skip = DisplayedActeurFactory(location=Point(-2.99, 47.66))
        DisplayedPropositionServiceFactory(action=reparer_action, acteur=skip)

        response = client.get(
            _url(),
            {"bbox": _bbox_around(-2.99, 47.66), "exclude_uuids": str(skip.uuid)},
        )
        assert response.status_code == 200
        payload = json.loads(response.content)
        uuids = {f["properties"]["uuid"] for f in payload["features"]}
        assert str(keep.uuid) in uuids
        assert str(skip.uuid) not in uuids

    def test_groupe_actions_filter_excludes_other_groups(self, client, reparer_action):
        keep = DisplayedActeurFactory(location=Point(-2.99, 47.66))
        DisplayedPropositionServiceFactory(action=reparer_action, acteur=keep)

        # Acteur whose only action belongs to a different groupe.
        other_group_action = (
            GroupeAction.objects.get(code="trier").actions.first()
        )
        skip = DisplayedActeurFactory(location=Point(-2.99, 47.66))
        DisplayedPropositionServiceFactory(action=other_group_action, acteur=skip)

        response = client.get(
            _url(),
            {
                "bbox": _bbox_around(-2.99, 47.66),
                "groupe_actions": str(reparer_action.groupe_action_id),
            },
        )
        assert response.status_code == 200
        payload = json.loads(response.content)
        uuids = {f["properties"]["uuid"] for f in payload["features"]}
        assert str(keep.uuid) in uuids
        assert str(skip.uuid) not in uuids

    def test_limit_caps_result_count(self, client, reparer_action):
        # Spread acteurs into distinct ~500 m grid cells so spatial thinning
        # (DISTINCT ON (ST_SnapToGrid(location, 0.005))) keeps all 5.
        for i in range(5):
            acteur = DisplayedActeurFactory(location=Point(-2.99 + i * 0.02, 47.66))
            DisplayedPropositionServiceFactory(action=reparer_action, acteur=acteur)

        response = client.get(
            _url(),
            {"bbox": _bbox_around(-2.99, 47.66, half=0.5), "limit": "3"},
        )
        payload = json.loads(response.content)
        assert len(payload["features"]) == 3

    def test_truncated_flag_when_limit_hit(self, client, reparer_action):
        # 5 acteurs in distinct grid cells, ask for at most 3.
        for i in range(5):
            acteur = DisplayedActeurFactory(location=Point(-2.99 + i * 0.02, 47.66))
            DisplayedPropositionServiceFactory(action=reparer_action, acteur=acteur)

        response = client.get(
            _url(),
            {"bbox": _bbox_around(-2.99, 47.66, half=0.5), "limit": "3"},
        )
        payload = json.loads(response.content)
        assert payload["truncated"] is True

    def test_truncated_flag_false_when_limit_not_hit(self, client, reparer_action):
        for i in range(2):
            acteur = DisplayedActeurFactory(location=Point(-2.99 + i * 0.02, 47.66))
            DisplayedPropositionServiceFactory(action=reparer_action, acteur=acteur)

        response = client.get(
            _url(),
            {"bbox": _bbox_around(-2.99, 47.66, half=0.5), "limit": "10"},
        )
        payload = json.loads(response.content)
        assert payload["truncated"] is False

    def test_low_zoom_spatial_thinning_uses_coarser_grid(self, client, reparer_action):
        # 5 acteurs spread ~10 km apart fall into distinct ~500 m cells (the
        # default grid) and would all pass through. At a low zoom, the grid
        # cell grows large enough that they all snap into one cell, so the
        # endpoint thins them down to 1.
        for i in range(5):
            acteur = DisplayedActeurFactory(location=Point(-2.99 + i * 0.1, 47.66))
            DisplayedPropositionServiceFactory(action=reparer_action, acteur=acteur)

        # Without zoom (default branch) all 5 are returned.
        response = client.get(_url(), {"bbox": _bbox_around(-2.99, 47.66, half=2.0)})
        assert len(json.loads(response.content)["features"]) == 5

        # At zoom 5 (~country level) the grid is much coarser and they all
        # snap into one cell.
        response = client.get(
            _url(),
            {"bbox": _bbox_around(-2.99, 47.66, half=2.0), "zoom": "5"},
        )
        assert len(json.loads(response.content)["features"]) == 1

    def test_spatial_thinning_dedups_clustered_acteurs(self, client, reparer_action):
        # 5 acteurs at the exact same location all snap into one grid cell;
        # the response should return at most 1 of them.
        for _ in range(5):
            acteur = DisplayedActeurFactory(location=Point(-2.99, 47.66))
            DisplayedPropositionServiceFactory(action=reparer_action, acteur=acteur)

        response = client.get(_url(), {"bbox": _bbox_around(-2.99, 47.66)})
        payload = json.loads(response.content)
        assert len(payload["features"]) == 1
