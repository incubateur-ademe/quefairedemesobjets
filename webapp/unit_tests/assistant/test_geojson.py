import json

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from core.constants import DIGITAL_ACTEUR_CODE
from qfdmo.models.acteur import MAX_PLACES_ON_MAP
from unit_tests.assistant.helpers import (
    PARIS,
    PARIS_POINT,
    action_of,
    fiche_for,
    place_offering,
)
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

pytestmark = pytest.mark.django_db


def get_lieux(client, **params):
    return client.get(reverse("api_v1:lieux-geojson"), {**PARIS, **params})


def features(client, **params):
    return json.loads(get_lieux(client, **params).content)["features"]


class TestParametres:
    """Invalid input is a 422 (django-ninja's convention), never a 500."""

    def test_returns_422_when_geste_missing(self, client):
        assert client.get(reverse("api_v1:lieux-geojson"), PARIS).status_code == 422

    def test_returns_422_when_position_missing(self, client):
        response = client.get(reverse("api_v1:lieux-geojson"), {"geste": "reparer"})
        assert response.status_code == 422

    def test_returns_422_on_non_numeric_coordinates(self, client):
        assert get_lieux(client, geste="reparer", latitude="ici").status_code == 422

    def test_returns_422_on_unreadable_bbox(self, client):
        assert get_lieux(client, geste="reparer", bbox="pas-du-json").status_code == 422

    def test_unreadable_bbox_does_not_fall_back_to_coordinates(self, client):
        """A fallback would hide a client bug and show another area."""
        assert get_lieux(client, geste="reparer", bbox="{}").status_code == 422

    @pytest.mark.parametrize(
        "bbox",
        [
            "[1,2]",
            '{"southWest":{"lng":"x","lat":1},"northEast":{"lng":2,"lat":3}}',
            '{"southWest":{"lng":1e400,"lat":1},"northEast":{"lng":2,"lat":3}}',
            '{"southWest":{"lng":200,"lat":1},"northEast":{"lng":2,"lat":3}}',
        ],
    )
    def test_returns_422_on_malformed_bbox_contents(self, client, bbox):
        assert get_lieux(client, geste="reparer", bbox=bbox).status_code == 422

    def test_returns_422_on_out_of_range_coordinates(self, client):
        assert get_lieux(client, geste="reparer", latitude="91").status_code == 422


class TestReponse:
    def test_serves_a_feature_collection(self, client, reparer):
        place_offering(reparer)

        payload = json.loads(get_lieux(client, geste="reparer").content)

        assert payload["type"] == "FeatureCollection"
        assert len(payload["features"]) == 1

    def test_an_unknown_geste_finds_no_place(self, client, reparer):
        place_offering(reparer)

        response = get_lieux(client, geste="inconnu")

        assert response.status_code == 200
        assert json.loads(response.content)["features"] == []

    def test_caps_results_at_twenty_places(self, client, reparer):
        for _ in range(MAX_PLACES_ON_MAP + 5):
            place_offering(reparer)

        assert len(features(client, geste="reparer")) == MAX_PLACES_ON_MAP

    def test_deduplicates_acteur_offering_several_actions_of_a_geste(self, client):
        """ "Donner" covers donner, échanger and rapporter: one place, once."""
        acteur = DisplayedActeurFactory(location=PARIS_POINT)
        for code in ("donner", "echanger", "rapporter"):
            DisplayedPropositionServiceFactory(
                acteur=acteur, action=action_of("donner_echanger_rapporter", code)
            )

        assert len(features(client, geste="donner_echanger_rapporter")) == 1

    def test_accepts_several_gestes(self, client):
        """A block of the fiche may span two gestes: the union is served."""
        place_offering(action_of("donner_echanger_rapporter", "donner"))
        place_offering(action_of("vendre_acheter", "revendre"))
        place_offering(action_of("trier"))

        lieux = features(client, geste=["donner_echanger_rapporter", "vendre_acheter"])

        assert len(lieux) == 2

    def test_a_single_geste_is_the_geste_of_every_place(self, client, reparer):
        place_offering(reparer)

        assert features(client, geste="reparer")[0]["properties"]["geste"] == "reparer"

    def test_draws_a_place_with_the_geste_it_offers(self, client):
        """On « donner ou revendre », a place that only sells is a vendre pin."""
        place_offering(action_of("vendre_acheter", "revendre"))

        lieux = features(client, geste=["donner_echanger_rapporter", "vendre_acheter"])

        assert lieux[0]["properties"]["geste"] == "vendre_acheter"

    def test_a_place_offering_both_gestes_takes_the_first_in_display_order(
        self, client
    ):
        acteur = place_offering(action_of("vendre_acheter", "revendre", order=4))
        DisplayedPropositionServiceFactory(
            acteur=acteur,
            action=action_of("donner_echanger_rapporter", "donner", order=2),
        )

        lieux = features(client, geste=["vendre_acheter", "donner_echanger_rapporter"])

        assert lieux[0]["properties"]["geste"] == "donner_echanger_rapporter"

    def test_the_geste_is_the_one_offered_for_the_object_of_the_fiche(self, client):
        """Giving bikes away does not make a phone reseller a donner pin."""
        telephone, velo = SousCategorieObjetFactory(), SousCategorieObjetFactory()
        acteur = place_offering(
            action_of("donner_echanger_rapporter", "donner"), sous_categories=[velo]
        )
        revente = DisplayedPropositionServiceFactory(
            acteur=acteur, action=action_of("vendre_acheter", "revendre")
        )
        revente.sous_categories.add(telephone)

        lieux = features(
            client,
            geste=["donner_echanger_rapporter", "vendre_acheter"],
            fiche=fiche_for([telephone]).slug,
        )

        assert lieux[0]["properties"]["geste"] == "vendre_acheter"

    def test_ignores_places_offering_another_geste(self, client, reparer):
        place_offering(action_of("trier"))

        assert features(client, geste="reparer") == []

    def test_orders_by_proximity(self, client, reparer):
        for longitude in (2.60, 2.40, 2.35):
            place_offering(reparer, at=Point(longitude, 48.8534, srid=4326))

        lieux = features(client, geste="reparer")

        longitudes = [feature["geometry"]["coordinates"][0] for feature in lieux]
        assert longitudes == [2.35, 2.40, 2.60]

    def test_exposes_only_what_the_map_needs(self, client, reparer):
        place_offering(reparer)

        lieux = features(client, geste="reparer")

        assert set(lieux[0]["properties"]) == {"uuid", "nom", "bonus", "geste"}

    def test_excludes_digital_acteurs(self, client, reparer):
        place_offering(reparer, acteur_type=ActeurTypeFactory(code=DIGITAL_ACTEUR_CODE))

        assert features(client, geste="reparer") == []

    def test_narrows_places_to_the_object_of_the_fiche(self, client, reparer):
        """A bike repairer is not a furniture repairer."""
        velo, meuble = SousCategorieObjetFactory(), SousCategorieObjetFactory()
        place_offering(reparer, sous_categories=[velo])
        chez_le_menuisier = place_offering(reparer, sous_categories=[meuble])

        lieux = features(client, geste="reparer", fiche=fiche_for([meuble]).slug)

        assert [lieu["properties"]["uuid"] for lieu in lieux] == [
            chez_le_menuisier.uuid
        ]

    def test_ignores_a_place_offering_the_object_under_another_geste(
        self, client, reparer
    ):
        """The geste and the objet must sit on the same proposition."""
        meuble = SousCategorieObjetFactory()
        place_offering(
            action_of("donner_echanger_rapporter", "donner"), sous_categories=[meuble]
        )

        lieux = features(client, geste="reparer", fiche=fiche_for([meuble]).slug)

        assert lieux == []

    def test_returns_404_on_unknown_object(self, client):
        assert get_lieux(client, geste="reparer", fiche="inconnu").status_code == 404

    def test_is_cacheable(self, client, reparer):
        place_offering(reparer)

        response = get_lieux(client, geste="reparer")

        assert "max-age" in response.headers["Cache-Control"]


class TestRequetes:
    def test_answers_in_a_single_query(
        self, client, reparer, django_assert_num_queries
    ):
        place_offering(reparer)

        with django_assert_num_queries(1):
            get_lieux(client, geste="reparer")

    def test_finds_the_geste_of_each_place_in_the_same_query(
        self, client, django_assert_num_queries
    ):
        place_offering(action_of("vendre_acheter", "revendre"))

        with django_assert_num_queries(1):
            get_lieux(client, geste=["donner_echanger_rapporter", "vendre_acheter"])
