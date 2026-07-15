import pytest
from django.core.management import call_command
from wagtail.models import Page, Site

from qfdmd.legacy_migration import migrate_produit
from qfdmd.models import HomePage, Produit

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Load fixtures once, outside test transactions."""
    with django_db_blocker.unblock():
        call_command("loaddata", "produits", "synonymes")


def _setup():
    root = Page.objects.get(depth=1)
    Site.objects.get_or_create(
        hostname="localhost",
        defaults={"root_page": root, "is_default_site": True},
    )
    if not HomePage.objects.filter(live=True).exists():
        homepage = HomePage(title="Accueil", slug="accueil")
        root.add_child(instance=homepage)
        homepage.save_revision().publish()
    return root


def _migrate(nom: str):
    _setup()
    produit = Produit.objects.get(nom=nom)
    report = migrate_produit(produit)
    return report, produit


class TestSyncFromLegacyProduit:
    def test_contenu_au_synonyme_avec_etat(self):
        """Appareil photo numerique: contenu au synonyme avec etat."""
        report, produit = _migrate("Appareil photo numérique")
        synonyme = produit.synonymes.filter(nom=produit.nom).first()
        assert synonyme is not None
        assert synonyme.qu_est_ce_que_j_en_fais_bon_etat
        assert synonyme.qu_est_ce_que_j_en_fais_mauvais_etat

        page = report.page
        assert page.live
        blocks = list(page.body)
        assert blocks[0].block_type == "item_grid"
        grid = blocks[0].value
        assert grid["column_width"] == "6"
        assert len(grid["items"]) == 2

        card1 = grid["items"][0].value
        assert card1["title"] == "Donner ou revendre"
        assert card1["heading_tag"] == "h3"
        badges1 = card1["top_detail_badges_tags"]
        assert badges1[0].block_type == "badges"
        badge1 = badges1[0].value[0].value
        assert badge1["text"] == "Bon état"
        assert badge1["color"] == "cumulus"
        assert synonyme.bon_etat in card1["description"].source

        card2 = grid["items"][1].value
        assert card2["title"] == "Déposer"
        badge2 = card2["top_detail_badges_tags"][0].value[0].value
        assert badge2["text"] == "Mauvais état"
        assert badge2["color"] == "glycine"
        assert synonyme.mauvais_etat in card2["description"].source

        break_blocks = [b for b in blocks if b.block_type == "break"]
        assert len(break_blocks) == 1
        after_break = blocks[blocks.index(break_blocks[0]) + 1 :]
        after_texts = " ".join(
            b.value.source if hasattr(b.value, "source") else str(b.value)
            for b in after_break
        )
        assert "Que va-t-il devenir" in after_texts
        assert "Comment consommer responsable" in after_texts
        assert "Dernière mise à jour" in after_texts
        if produit.liens.exists():
            assert "En savoir plus" in after_texts

        assert page.seo_title == f"Que faire de mon {produit.nom}"
        assert page.search_description == synonyme.meta_description

    def test_contenu_au_produit_avec_etat(self):
        """Materiaux du batiment en pierre: contenu au produit avec etat."""
        report, produit = _migrate("Matériaux du bâtiment en pierre")
        assert produit.qu_est_ce_que_j_en_fais_bon_etat
        assert produit.qu_est_ce_que_j_en_fais_mauvais_etat

        page = report.page
        assert page.live
        blocks = list(page.body)
        grid = blocks[0].value
        card1 = grid["items"][0].value
        card2 = grid["items"][1].value
        assert card1["title"] == "Donner ou revendre"
        assert card2["title"] == "Déposer"
        assert produit.bon_etat in card1["description"].source
        assert produit.mauvais_etat in card2["description"].source
        assert page.search_description
        assert page.seo_title

    def test_sans_etat(self):
        """Aiguille usagee (medicale): sans etat, simple paragraph."""
        report, produit = _migrate("Aiguille usagée (médicale)")
        assert produit.qu_est_ce_que_j_en_fais

        page = report.page
        assert page.live
        blocks = list(page.body)
        assert blocks[0].block_type == "paragraph"
        assert produit.qu_est_ce_que_j_en_fais in blocks[0].value.source
        assert not any(b.block_type == "item_grid" for b in blocks)

        break_blocks = [b for b in blocks if b.block_type == "break"]
        assert len(break_blocks) == 1
        after_break = blocks[blocks.index(break_blocks[0]) + 1 :]
        after_texts = " ".join(
            b.value.source if hasattr(b.value, "source") else str(b.value)
            for b in after_break
        )
        assert "Que va-t-il devenir" in after_texts
        assert "Dernière mise à jour" in after_texts
