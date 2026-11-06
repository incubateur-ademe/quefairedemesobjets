"""Selection of the places shared by every endpoint listing them."""

import json

import pytest
from django.contrib.gis.geos import Point
from pydantic import ValidationError

from qfdmo.lieux_query import LieuxQuery
from qfdmo.models.acteur import DisplayedActeur, acteur_ids_offering
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

pytestmark = pytest.mark.django_db

PARIS_BBOX = [2.30, 48.83, 2.40, 48.88]


@pytest.fixture
def reparer():
    groupe = GroupeActionFactory(code="reparer")
    return ActionFactory(code="reparer", groupe_action=groupe)


def place(action, longitude=2.35, latitude=48.85, sous_categories=()):
    acteur = DisplayedActeurFactory(location=Point(longitude, latitude, srid=4326))
    proposition = DisplayedPropositionServiceFactory(acteur=acteur, action=action)
    proposition.sous_categories.add(*sous_categories)
    return acteur


def acteurs():
    return DisplayedActeur.objects.all()


class TestProposing:
    def test_geste_and_objet_are_matched_on_the_same_proposition(self, reparer):
        donner = ActionFactory(
            code="donner", groupe_action=GroupeActionFactory(code="donner")
        )
        velo, meuble = SousCategorieObjetFactory(), SousCategorieObjetFactory()
        repairer = place(reparer, sous_categories=[meuble])
        mixed = place(reparer, sous_categories=[velo])
        DisplayedPropositionServiceFactory(
            acteur=mixed, action=donner
        ).sous_categories.add(meuble)

        assert list(acteurs().proposing(["reparer"], [meuble.id])) == [repairer]

    def test_several_matching_propositions_list_the_acteur_once(self, reparer):
        acteur = place(reparer)
        DisplayedPropositionServiceFactory(acteur=acteur, action=reparer)

        assert list(acteurs().proposing(["reparer"])) == [acteur]

    def test_a_cached_too_many_answer_is_not_recomputed(
        self, reparer, django_assert_num_queries, monkeypatch, settings
    ):
        settings.CACHES = {
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
        }
        monkeypatch.setattr("qfdmo.models.acteur.GEOGRAPHIC_SCAN_THRESHOLD", 0)
        meuble = SousCategorieObjetFactory()
        place(reparer, sous_categories=[meuble])

        assert acteur_ids_offering(["reparer"], [meuble.id]) is None
        with django_assert_num_queries(0):
            assert acteur_ids_offering(["reparer"], [meuble.id]) is None


class TestPosition:
    def test_within_keeps_the_area_and_orders_from_its_center(self, reparer):
        far_in = place(reparer, longitude=2.31)
        near_in = place(reparer, longitude=2.35, latitude=48.855)
        place(reparer, longitude=2.60)

        assert list(acteurs().within(PARIS_BBOX)) == [near_in, far_in]

    def test_nearest_to_orders_by_distance(self, reparer):
        far = place(reparer, longitude=2.60)
        near = place(reparer, longitude=2.36)

        assert list(acteurs().nearest_to(2.35, 48.85)) == [near, far]

    def test_the_indexed_operators_are_used(self):
        """`within` and a distance bound would both bypass the GiST index."""
        within_sql = str(acteurs().within(PARIS_BBOX).query)
        nearest_sql = str(acteurs().nearest_to(2.35, 48.85).query)

        assert "&&" in within_sql and "ST_Within" not in within_sql
        assert "<->" in nearest_sql and "ST_DWithin" not in nearest_sql


def bbox(west, south, east, north):
    return json.dumps(
        {
            "southWest": {"lng": west, "lat": south},
            "northEast": {"lng": east, "lat": north},
        }
    )


class TestLieuxQuery:
    def test_reads_the_bbox_of_the_map(self):
        query = LieuxQuery(geste=["reparer"], bbox=bbox(*PARIS_BBOX))

        assert query.bbox == PARIS_BBOX

    @pytest.mark.parametrize(
        "raw", ["pas du json", '{"southWest": {}}', bbox(2.3, 48.8, 200, 48.9)]
    )
    def test_an_unreadable_or_out_of_range_bbox_is_refused(self, raw):
        with pytest.raises(ValidationError):
            LieuxQuery(geste=["reparer"], bbox=raw, longitude=2.35, latitude=48.85)

    def test_the_bbox_wins_over_the_point(self, reparer):
        in_view = place(reparer, longitude=2.35)
        place(reparer, longitude=5.0)

        query = LieuxQuery(
            geste=["reparer"], bbox=bbox(*PARIS_BBOX), longitude=5.0, latitude=48.85
        )

        assert list(query.queryset()) == [in_view]

    @pytest.mark.parametrize("geste", [[], ["", " "]])
    def test_a_geste_is_required(self, geste):
        with pytest.raises(ValidationError):
            LieuxQuery(geste=geste, longitude=2.35, latitude=48.85)

    def test_a_position_is_required(self):
        with pytest.raises(ValidationError):
            LieuxQuery(geste=["reparer"])
