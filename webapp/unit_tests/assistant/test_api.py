"""API v1 endpoints of the assistant's screens."""

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from qfdmo.models.acteur import DataLicense
from unit_tests.assistant.helpers import PARIS, place_offering, rename_search_term

pytestmark = pytest.mark.django_db


class TestObjets:
    def test_too_short_query_yields_nothing(self, client):
        assert client.get(reverse("api_v1:objets"), {"q": "a"}).json() == {
            "results": []
        }

    @pytest.mark.parametrize(
        "searchable_title,label",
        [
            ("Bidule test", "Bidule test"),
            # Synonymes are typed in lower case in the CMS.
            ("bidule en grès", "Bidule en grès"),
        ],
    )
    def test_suggests_a_fiche_with_its_slug_and_a_capitalized_label(
        self, client, fiche, searchable_title, label
    ):
        rename_search_term(fiche, searchable_title)

        results = client.get(reverse("api_v1:objets"), {"q": "bidule"}).json()[
            "results"
        ]

        assert {"label": label, "slug": fiche.slug} in results


class TestLieuxGeojson:
    def test_the_map_keeps_every_source(self, client, reparer):
        """The GeoJSON is what the assistant draws, not what is redistributed."""
        place_offering(reparer, licence=DataLicense.NO_LICENSE)

        payload = client.get(
            reverse("api_v1:lieux-geojson"), {**PARIS, "geste": "reparer"}
        ).json()

        assert len(payload["features"]) == 1

    def test_around_a_point_only_the_places_within_20_km(self, client, reparer):
        near = place_offering(
            reparer,
            at=Point(2.3488, 48.95, srid=4326),  # ~11 km north
            licence=DataLicense.OPEN_LICENSE,
        )
        place_offering(
            reparer,
            at=Point(2.3488, 49.10, srid=4326),  # ~27 km north
            licence=DataLicense.OPEN_LICENSE,
        )

        payload = client.get(
            reverse("api_v1:lieux-geojson"), {**PARIS, "geste": "reparer"}
        ).json()

        assert [feature["properties"]["uuid"] for feature in payload["features"]] == [
            near.uuid
        ]
