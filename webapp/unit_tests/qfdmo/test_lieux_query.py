"""The places query shared by the assistant's map and the open data."""

import pytest
from django.contrib.gis.geos import Point

from qfdmo.models.acteur import DisplayedActeur
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

pytestmark = pytest.mark.django_db

PARIS_POINT = Point(2.3488, 48.8534, srid=4326)


class TestRequetes:
    def test_within_uses_the_indexed_bounding_box_operator(self):
        """`within` on a geography column ignores the index and costs 2 s."""
        sql = str(
            DisplayedActeur.objects.all()
            .proposing("reparer")
            .within([2.30, 48.83, 2.40, 48.88])
            .query
        )
        assert "&&" in sql
        assert "ST_Within" not in sql

    def test_lists_candidates_when_the_geste_object_pair_is_rare(self):
        """Without the list, a rare pair scans 388,000 acteurs."""
        groupe = GroupeActionFactory(code="reparer")
        action = ActionFactory(code="reparer", groupe_action=groupe)
        meuble = SousCategorieObjetFactory()
        acteur = DisplayedActeurFactory(location=PARIS_POINT)
        proposition = DisplayedPropositionServiceFactory(acteur=acteur, action=action)
        proposition.sous_categories.add(meuble)

        sql = str(DisplayedActeur.objects.all().proposing("reparer", [meuble.id]).query)
        assert "identifiant_unique" in sql
        assert "EXISTS" not in sql.upper()

    def test_nearest_to_does_not_bound_the_search(self):
        """A distance bound would prevent the ordered index scan."""
        sql = str(
            DisplayedActeur.objects.all()
            .proposing("reparer")
            .nearest_to(2.3488, 48.8534)
            .query
        )
        assert "ST_DWithin" not in sql
        assert "<->" in sql


class TestDocumentation:
    def test_the_v1_api_has_its_own_documentation(self, client):
        assert client.get("/api/v1/docs").status_code == 200

    def test_the_historical_api_still_answers(self, client):
        assert client.get("/api/docs").status_code == 200
