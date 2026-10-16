"""Open data of the places: the perimeter and the columns of data.ademe.fr."""

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from opendata.lieux import open_data
from qfdmo.models.acteur import DataLicense, DisplayedActeur
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

pytestmark = pytest.mark.django_db

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


def get_lieu(client, acteur):
    return client.get(reverse("api_v1:lieu", args=[acteur.uuid]))


class TestOpenData:
    def test_a_parent_with_one_open_child_is_served(self):
        """`sources` of a parent holds its children's sources: one open is enough."""
        parent = DisplayedActeurFactory(location=PARIS_POINT)
        parent.sources.add(
            SourceFactory(licence=DataLicense.NO_LICENSE),
            SourceFactory(licence=DataLicense.OPEN_LICENSE),
        )

        assert list(open_data(DisplayedActeur.objects.all())) == [parent]


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

    def test_serves_the_columns_of_the_dataset(self, client, reparer):
        acteur = place(reparer)

        item = get_lieu(client, acteur).json()

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

        item = get_lieu(client, acteur).json()

        assert item["paternite"] == "Que faire de mes objets et déchets|ADEME|Alpha|Zed"

    def test_propositions_carry_action_and_sous_categories(self, client, reparer):
        from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

        acteur = place(reparer)
        proposition = acteur.proposition_services.get()
        proposition.sous_categories.add(SousCategorieObjetFactory(code="velo"))

        item = get_lieu(client, acteur).json()

        assert item["propositions_de_services"] == [
            {"action": "reparer", "sous_categories": ["velo"]}
        ]

    def test_the_bonus_reparation_comes_from_the_labels(self, client, reparer):
        acteur = place(reparer)
        acteur.labels.add(LabelQualiteFactory(bonus=True, code="bonusrepar"))

        item = get_lieu(client, acteur).json()

        assert item["propose_le_bonus_reparation"] is True
        assert item["qualites_et_labels"] == "bonusrepar"


class TestGestes:
    def test_lists_the_groupes_in_display_order(self, client):
        """The fixtures load the five groupes: the API serves them, in order."""
        from qfdmo.models.action import GroupeAction

        payload = client.get(reverse("api_v1:gestes")).json()

        expected = list(GroupeAction.objects.order_by("order"))
        assert [geste["code"] for geste in payload] == [g.code for g in expected]
        assert payload[0]["couleur"] == expected[0].couleur
        assert set(payload[0]) == {"code", "libelle", "libelle_court", "couleur"}
