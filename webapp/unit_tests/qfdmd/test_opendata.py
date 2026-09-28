"""The open data of the fiches: two tables, the conventions of the acteurs CSV."""

import csv
from io import StringIO

import pytest
from django.urls import reverse
from django.utils import timezone
from wagtail.models import Site

from qfdmd.models import LieuDeDepot
from qfdmd.opendata import (
    CONSIGNE_COLUMNS,
    PRODUIT_COLUMNS,
    consigne_rows,
    plain_text,
    produit_row,
    write_csv,
)
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
from unit_tests.qfdmd.test_consignes_block import consigne, grid, page_with
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def home():
    """The root of the default site: pages below it have a full URL."""
    return Site.objects.get(is_default_site=True).root_page


@pytest.fixture
def famille(home):
    return ProduitPageFactory(
        parent=home, title="Emballages", slug="emballages", est_famille=True
    )


@pytest.fixture
def fiche(famille):
    bac = LieuDeDepot.objects.get(code="bac_de_tri")
    page = page_with(
        grid(
            consigne(
                "Réparer",
                id="rep",
                contenu=(
                    "<p>Un <b>réparateur</b></p><ul><li>près de chez vous</li></ul>"
                ),
                etat="reparable",
                bonus_reparation=True,
                gestes=["reparer"],
            ),
            consigne("Au bac", id="bac", lieu_de_depot=bac.pk, gestes=["trier"]),
        ),
        parent=famille,
        title="Pot de yaourt",
        slug="pot-de-yaourt",
        usage_unique=True,
        live=True,
        last_published_at=timezone.now(),
    )
    page.search_tags.add("yaourt", "pot")
    page.sous_categorie_objet.add(
        SousCategorieObjetFactory(code="emballage_plastique"),
        SousCategorieObjetFactory(code="emballage_carton"),
    )
    page.save()
    return page


class TestProduitRow:
    def test_columns_and_pivots(self, fiche, famille):
        row = produit_row(fiche)

        assert list(row) == PRODUIT_COLUMNS
        assert row["identifiant"] == fiche.pk
        assert row["nom"] == "Pot de yaourt"
        assert row["url"].endswith("/emballages/pot-de-yaourt/")
        assert row["type"] == "dechet"
        assert row["identifiant_famille"] == famille.pk
        assert row["synonymes"] == "pot|yaourt"
        assert row["sous_categories"] == "emballage_carton|emballage_plastique"
        assert row["date_de_derniere_modification"] == timezone.now().date().isoformat()

    def test_a_famille_under_the_home_has_no_parent_famille(self, famille):
        row = produit_row(famille)

        assert row["type"] == "objet"
        assert row["identifiant_famille"] is None
        assert row["date_de_derniere_modification"] == ""


class TestConsigneRows:
    def test_one_row_per_consigne_in_reading_order(self, fiche):
        rows = consigne_rows(fiche)

        assert [list(row) for row in rows] == [CONSIGNE_COLUMNS] * 2
        assert [row["ordre"] for row in rows] == [1, 2]
        assert [row["identifiant"] for row in rows] == ["rep", "bac"]
        assert {row["identifiant_produit"] for row in rows} == {fiche.pk}

    def test_typed_fields_are_codes(self, fiche):
        reparer, bac = consigne_rows(fiche)

        assert reparer["gestes"] == "reparer"
        assert reparer["etat"] == "reparable"
        assert reparer["bonus_reparation"] is True
        assert reparer["lieu_de_depot"] == ""
        assert bac["etat"] == ""
        assert bac["lieu_de_depot"] == "bac_de_tri"
        assert bac["bonus_reparation"] is False

    def test_the_content_comes_rich_and_plain(self, fiche):
        reparer = consigne_rows(fiche)[0]

        assert reparer["contenu"].startswith("<p>Un <b>réparateur</b></p>")
        assert reparer["contenu_texte"] == "Un réparateur\n- près de chez vous"


class TestPlainText:
    def test_lists_keep_a_dash_per_item(self):
        html = "<p>Deux &amp; trois :</p><ol><li>un</li><li>deux</li></ol>"

        assert plain_text(html) == "Deux & trois :\n- un\n- deux"


class TestWriteCsv:
    def test_booleans_and_missing_values_as_the_acteurs_csv(self):
        stream = StringIO()

        write_csv(
            [{"a": True, "b": None, "c": 3}, {"a": False, "b": "x", "c": ""}],
            ["a", "b", "c"],
            stream,
        )

        assert list(csv.reader(StringIO(stream.getvalue()))) == [
            ["a", "b", "c"],
            ["true", "", "3"],
            ["false", "x", ""],
        ]


class TestApi:
    def test_produits_are_paginated_rows(self, client, fiche):
        payload = client.get(reverse("api_v1:produits")).json()

        assert payload["count"] >= 2
        identifiants = {item["identifiant"] for item in payload["items"]}
        assert fiche.pk in identifiants
        assert set(payload["items"][0]) == set(PRODUIT_COLUMNS)

    def test_consignes_are_paginated_rows(self, client, fiche):
        payload = client.get(reverse("api_v1:consignes")).json()

        assert [item["identifiant"] for item in payload["items"]] == ["rep", "bac"]
        assert set(payload["items"][0]) == set(CONSIGNE_COLUMNS)
        assert payload["items"][0]["bonus_reparation"] is True

    def test_the_csv_carries_the_same_columns(self, client, fiche):
        response = client.get(reverse("api_v1:consignes-csv"))

        assert response["Content-Type"].startswith("text/csv")
        rows = list(csv.DictReader(StringIO(response.content.decode())))
        assert list(rows[0]) == CONSIGNE_COLUMNS
        assert rows[0]["bonus_reparation"] == "true"
        assert rows[1]["etat"] == ""

    def test_the_produits_csv(self, client, fiche):
        rows = list(
            csv.DictReader(
                StringIO(client.get(reverse("api_v1:produits-csv")).content.decode())
            )
        )

        assert list(rows[0]) == PRODUIT_COLUMNS
        assert any(row["nom"] == "Pot de yaourt" for row in rows)
