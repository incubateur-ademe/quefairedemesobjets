import json

import pytest

from qfdmd.models import LieuDeDepot
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

pytestmark = pytest.mark.django_db


def consigne(titre, id="00000000-0000-0000-0000-000000000000", **extra):
    """A list item as the CMS stores it, id included."""
    return {
        "type": "item",
        "id": id,
        "value": {
            "titre": titre,
            "contenu": f"<p>{titre}</p>",
            "gestes": ["donner"],
            **extra,
        },
    }


def grid(*consignes, column_width="4"):
    return {
        "type": "consignes",
        "value": {"column_width": column_width, "consignes": list(consignes)},
    }


def paragraph(text):
    return {"type": "paragraph", "value": f"<p>{text}</p>"}


def page_with(*blocks, **kwargs):
    """Raw JSON, as read from the database: the values go through the
    blocks' normalisation, unlike Python values handed to the factory."""
    return ProduitPageFactory(body=json.dumps(list(blocks)), **kwargs)


class TestProduitPageConsignes:
    def test_consignes_are_read_across_grids_in_page_order(self):
        """The export and the assistant read one flat list, whatever the
        number of grids and the content around them."""
        page = page_with(
            paragraph("Intro"),
            grid(consigne("A"), consigne("B")),
            paragraph("Entre deux"),
            grid(consigne("C")),
        )

        assert [c.value["titre"] for c in page.consignes] == ["A", "B", "C"]

    def test_each_consigne_keeps_the_identifier_of_the_cms(self):
        page = page_with(grid(consigne("A", id="a-1"), consigne("B", id="b-2")))

        assert [c.id for c in page.consignes] == ["a-1", "b-2"]

    def test_a_page_without_grid_has_no_consignes(self):
        page = page_with(paragraph("Rien"))

        assert page.consignes == []

    def test_a_consigne_keeps_its_etat_lieu_bonus_and_gestes(self):
        bac = LieuDeDepot.objects.get(code="bac_de_tri")
        page = page_with(
            grid(
                consigne(
                    "Réparer",
                    etat="reparable",
                    bonus_reparation=True,
                    gestes=["reparer"],
                ),
                consigne("Déposer", lieu_de_depot=bac.pk, gestes=["trier"]),
            )
        )

        reparer, deposer = (c.value for c in page.consignes)
        assert reparer["etat"] == "reparable"
        assert reparer["bonus_reparation"] is True
        assert reparer["gestes"] == ["reparer"]
        assert not deposer["etat"]
        assert deposer["lieu_de_depot"] == bac
        assert deposer["gestes"] == ["trier"]


class TestGestesChoices:
    def test_every_action_is_offered_even_hidden_from_the_carte(self):
        """`afficher` is a carte flag: `trier` is off there in production, and
        it is the geste of every déchet consigne."""
        from qfdmd.blocks import action_choices
        from qfdmo.models.action import Action

        Action.objects.filter(code="trier").update(afficher=False)

        assert "trier" in dict(action_choices())


class TestLieuDeDepot:
    def test_str_is_the_libelle(self):
        assert str(LieuDeDepot(code="bac_de_tri", libelle="Bac de tri")) == "Bac de tri"


class TestConsignesRendering:
    def test_the_grid_renders_cards_with_badges(self):
        bac = LieuDeDepot.objects.get(code="bac_de_tri")
        page = page_with(
            grid(
                consigne(
                    "Réparer",
                    etat="reparable",
                    bonus_reparation=True,
                    gestes=["reparer"],
                ),
                consigne("Déposer", lieu_de_depot=bac.pk, gestes=["trier"]),
            )
        )

        html = str(page.body)

        assert html.count("fr-card__title") == 2
        # The chosen width, 4/12 by default.
        assert "fr-col-md-4" in html
        assert "Réparable" in html
        assert "Bonus réparation" in html
        assert "fr-badge--yellow-tournesol" in html
        assert "Bac de tri" in html
