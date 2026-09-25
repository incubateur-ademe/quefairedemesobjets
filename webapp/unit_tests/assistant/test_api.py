"""The public API v1: same engine as the screens, opendata perimeter."""

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from qfdmo.models.acteur import DataLicense, DisplayedActeur
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

pytestmark = pytest.mark.django_db

PARIS = {"latitude": "48.8534", "longitude": "2.3488"}
PARIS_POINT = Point(2.3488, 48.8534, srid=4326)

# The columns of the CSV published on data.ademe.fr that the API serves.
OPENDATA_COLUMNS = {
    "identifiant",
    "paternite",
    "nom",
    "nom_commercial",
    "siren",
    "siret",
    "description",
    "type_dacteur",
    "site_web",
    "telephone",
    "adresse",
    "complement_dadresse",
    "code_postal",
    "ville",
    "code_commune",
    "code_epci",
    "nom_epci",
    "latitude",
    "longitude",
    "qualites_et_labels",
    "propose_le_bonus_reparation",
    "public_accueilli",
    "reprise",
    "exclusivite_de_reprisereparation",
    "uniquement_sur_rdv",
    "type_de_services",
    "lieu_prestation",
    "perimetreadomicile",
    "consignes_dacces",
    "horaires_description",
    "horaires_osm",
    "propositions_de_services",
    "date_de_derniere_modification",
}


@pytest.fixture
def reparer():
    groupe = GroupeActionFactory(code="reparer", libelle_court="Réparer")
    return ActionFactory(code="reparer", groupe_action=groupe)


def place(action, *, licence=DataLicense.OPEN_LICENSE, at=PARIS_POINT):
    acteur = DisplayedActeurFactory(location=at)
    acteur.sources.add(SourceFactory(licence=licence))
    DisplayedPropositionServiceFactory(acteur=acteur, action=action)
    return acteur


def get_lieux(client, **params):
    return client.get(reverse("api_v1:lieux"), {**PARIS, **params})


class TestOpenData:
    def test_only_open_licence_sources_are_served(self, client, reparer):
        """The perimeter of the dataset on data.ademe.fr."""
        open_place = place(reparer)
        place(reparer, licence=DataLicense.NO_LICENSE)

        payload = get_lieux(client, geste="reparer").json()

        assert [item["identifiant"] for item in payload["items"]] == [open_place.uuid]

    def test_a_parent_with_one_open_child_is_served(self):
        """`sources` of a parent holds its children's sources: one open is enough."""
        parent = DisplayedActeurFactory(location=PARIS_POINT)
        parent.sources.add(
            SourceFactory(licence=DataLicense.NO_LICENSE),
            SourceFactory(licence=DataLicense.OPEN_LICENSE),
        )

        assert list(DisplayedActeur.objects.all().open_data()) == [parent]

    def test_the_map_keeps_every_source(self, client, reparer):
        """The GeoJSON is what the assistant draws, not what is redistributed."""
        place(reparer, licence=DataLicense.NO_LICENSE)

        payload = client.get(
            reverse("api_v1:lieux-geojson"), {**PARIS, "geste": "reparer"}
        ).json()

        assert len(payload["features"]) == 1


class TestLieux:
    def test_serves_the_columns_of_the_dataset(self, client, reparer):
        place(reparer)

        item = get_lieux(client, geste="reparer").json()["items"][0]

        assert set(item) == OPENDATA_COLUMNS

    def test_paternite_names_the_site_then_the_open_sources(self, client, reparer):
        acteur = place(reparer)
        acteur.sources.set(
            [
                SourceFactory(libelle="Zed", licence=DataLicense.OPEN_LICENSE),
                SourceFactory(libelle="Alpha", licence=DataLicense.OPEN_LICENSE),
                SourceFactory(libelle="Fermée", licence=DataLicense.NO_LICENSE),
            ]
        )

        item = get_lieux(client, geste="reparer").json()["items"][0]

        assert item["paternite"] == "Que faire de mes objets et déchets|ADEME|Alpha|Zed"

    def test_propositions_carry_action_and_sous_categories(self, client, reparer):
        from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

        acteur = place(reparer)
        proposition = acteur.proposition_services.get()
        proposition.sous_categories.add(SousCategorieObjetFactory(code="velo"))

        item = get_lieux(client, geste="reparer").json()["items"][0]

        assert item["propositions_de_services"] == [
            {"action": "reparer", "sous_categories": ["velo"]}
        ]

    def test_the_bonus_reparation_comes_from_the_labels(self, client, reparer):
        acteur = place(reparer)
        acteur.labels.add(LabelQualiteFactory(bonus=True, code="bonusrepar"))

        item = get_lieux(client, geste="reparer").json()["items"][0]

        assert item["propose_le_bonus_reparation"] is True
        assert item["qualites_et_labels"] == "bonusrepar"

    def test_orders_by_proximity_and_paginates(self, client, reparer):
        for longitude in (2.60, 2.40, 2.35):
            place(reparer, at=Point(longitude, 48.8534, srid=4326))

        payload = get_lieux(client, geste="reparer", limit=2).json()

        assert payload["count"] == 3
        assert [item["longitude"] for item in payload["items"]] == [2.35, 2.40]

    def test_answers_in_a_bounded_number_of_queries(
        self, client, reparer, django_assert_max_num_queries
    ):
        """Every relation is prefetched: more places must not mean more queries."""
        for _ in range(3):
            place(reparer)

        # count, places, then one query per prefetched relation.
        with django_assert_max_num_queries(12):
            get_lieux(client, geste="reparer")

    def test_unknown_fiche_is_a_404(self, client, reparer):
        assert get_lieux(client, geste="reparer", fiche="inconnu").status_code == 404

    def test_position_is_required(self, client, reparer):
        assert (
            client.get(reverse("api_v1:lieux"), {"geste": "reparer"}).status_code == 422
        )


class TestLieu:
    def test_serves_an_open_place(self, client, reparer):
        acteur = place(reparer)

        response = client.get(reverse("api_v1:lieu", args=[acteur.uuid]))

        assert response.status_code == 200
        assert response.json()["identifiant"] == acteur.uuid

    def test_a_closed_place_is_not_found(self, client, reparer):
        acteur = place(reparer, licence=DataLicense.NO_LICENSE)

        response = client.get(reverse("api_v1:lieu", args=[acteur.uuid]))

        assert response.status_code == 404


class TestGestes:
    def test_lists_the_groupes_in_display_order(self, client):
        """The fixtures load the five groupes: the API serves them, in order."""
        from qfdmo.models.action import GroupeAction

        payload = client.get(reverse("api_v1:gestes")).json()

        expected = list(GroupeAction.objects.order_by("order"))
        assert [geste["code"] for geste in payload] == [g.code for g in expected]
        assert payload[0]["couleur"] == expected[0].couleur
        assert set(payload[0]) == {"code", "libelle", "libelle_court", "couleur"}


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


class TestDocumentation:
    def test_the_v1_api_has_its_own_documentation(self, client):
        assert client.get("/api/v1/docs").status_code == 200

    def test_the_historical_api_still_answers(self, client):
        assert client.get("/api/docs").status_code == 200
