"""API v1 endpoints of the assistant's screens."""

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from qfdmo.models.acteur import DataLicense
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

pytestmark = pytest.mark.django_db

PARIS = {"latitude": "48.8534", "longitude": "2.3488"}
PARIS_POINT = Point(2.3488, 48.8534, srid=4326)


@pytest.fixture
def reparer():
    groupe = GroupeActionFactory(code="reparer", libelle_court="Réparer")
    return ActionFactory(code="reparer", groupe_action=groupe)


def place(action, *, licence=DataLicense.OPEN_LICENSE, at=PARIS_POINT):
    acteur = DisplayedActeurFactory(location=at)
    acteur.sources.add(SourceFactory(licence=licence))
    DisplayedPropositionServiceFactory(acteur=acteur, action=action)
    return acteur


class TestLieuxGeojsonSources:
    def test_the_map_keeps_every_source(self, client, reparer):
        """The GeoJSON is what the assistant draws, not what is redistributed."""
        place(reparer, licence=DataLicense.NO_LICENSE)

        payload = client.get(
            reverse("api_v1:lieux-geojson"), {**PARIS, "geste": "reparer"}
        ).json()

        assert len(payload["features"]) == 1


class TestObjets:
    def test_too_short_query_yields_nothing(self, client):
        assert client.get(reverse("api_v1:objets"), {"q": "a"}).json() == {
            "results": []
        }

    def test_suggests_a_fiche_with_its_slug(self, client):
        from qfdmd.models import ProduitPageSearchTerm
        from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

        fiche = ProduitPageFactory(parent=None)
        term = ProduitPageSearchTerm.objects.get(produit_page=fiche)
        term.searchable_title = "Bidule test"
        term.save()

        results = client.get(reverse("api_v1:objets"), {"q": "bidule"}).json()[
            "results"
        ]

        assert {"label": "Bidule test", "slug": fiche.slug} in results


class TestLieuxGeojson:
    def test_around_a_point_only_the_places_within_20_km(self, client, reparer):
        """The map's first display: the nearest places, within 20 km (#3356)."""
        near = place(reparer, at=Point(2.3488, 48.95, srid=4326))  # ~11 km north
        place(reparer, at=Point(2.3488, 49.10, srid=4326))  # ~27 km north

        payload = client.get(
            reverse("api_v1:lieux-geojson"), {**PARIS, "geste": "reparer"}
        ).json()

        assert [feature["properties"]["uuid"] for feature in payload["features"]] == [
            near.uuid
        ]
