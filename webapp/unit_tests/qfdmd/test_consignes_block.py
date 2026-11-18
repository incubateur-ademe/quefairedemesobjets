import pytest

from qfdmd.models import LieuDeDepot
from unit_tests.qfdmd.helpers import consigne, grid, page_with, paragraph

pytestmark = pytest.mark.django_db


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
        page = page_with(
            grid(consigne("A", block_id="a-1"), consigne("B", block_id="b-2"))
        )

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
        assert "% Bonus Réparation" in html
        assert "fr-badge--yellow-tournesol" in html
        assert "Bac de tri" in html

    @pytest.mark.parametrize(
        "etat,couleur",
        [
            ("reparable", "green-menthe"),
            ("bon_etat", "blue-cumulus"),
            ("mauvais_etat", "purple-glycine"),
        ],
    )
    def test_each_etat_has_the_color_of_the_site(self, etat, couleur):
        """Retour de test : the colours of the badges in production."""
        html = str(page_with(grid(consigne("Titre", etat=etat))).body)

        assert f"fr-badge--{couleur}" in html

    def test_the_bonus_badge_is_tilleul_verveine(self):
        html = str(page_with(grid(consigne("Réparer", bonus_reparation=True))).body)

        assert "fr-badge--green-tilleul-verveine" in html

    def test_a_bare_text_content_stays_under_the_title(self):
        """Migrated text consignes are not wrapped in <p>: as anonymous flex
        items of the DSFR card they came before the title (order 2)."""
        item = consigne("Déposer")
        item["value"]["contenu"] = "Apportez-le en déchèterie."

        html = str(page_with(grid(item)).body)

        desc = html.index('class="fr-card__desc')
        assert desc < html.index("Apportez-le en déchèterie.")


class TestConsignesFilter:
    """Retour de test : retrouver dans Wagtail les fiches que la migration
    n'a pas converties."""

    def test_splits_the_fiches_on_their_grid(self):
        from qfdmd.models import ProduitPage
        from qfdmd.views import ConsignesFilter

        with_grid = page_with(paragraph("intro"), grid(consigne("Déposer")))
        without = page_with(paragraph("intro"))
        pages = ProduitPage.objects.filter(pk__in=[with_grid.pk, without.pk])

        assert list(ConsignesFilter().filter(pages, "sans")) == [without]
        assert list(ConsignesFilter().filter(pages, "avec")) == [with_grid]
        assert ConsignesFilter().filter(pages, "").count() == 2
