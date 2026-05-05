from unittest.mock import MagicMock

import pytest
from wagtail.models import Page, Site

from core.templatetags.carte_tags import carte
from qfdmd.models import ProduitIndexPage, ProduitPage
from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


@pytest.fixture
def wagtail_site():
    root_page = Page.objects.get(depth=1)
    site, _ = Site.objects.get_or_create(
        hostname="testserver",
        defaults={
            "root_page": root_page,
            "is_default_site": True,
            "site_name": "Test Site",
        },
    )
    if site.root_page != root_page:
        site.root_page = root_page
        site.save()
    return site


@pytest.fixture
def produit_index(wagtail_site):
    index = ProduitIndexPage(title="Catégories", slug="categories")
    wagtail_site.root_page.add_child(instance=index)
    return index


@pytest.fixture
def produit_page(produit_index):
    page = ProduitPage(title="Vêtements", slug="vetements")
    produit_index.add_child(instance=page)
    return page


@pytest.fixture
def produit_page_ab_enabled(produit_index):
    page = ProduitPage(
        title="Meubles",
        slug="meubles",
        ab_test_carte_default_view=True,
    )
    produit_index.add_child(instance=page)
    return page


@pytest.mark.django_db
class TestCarteTag:
    def test_returns_url_variant_with_view_mode_liste(self, produit_page):
        carte_config = CarteConfigFactory(slug="carte-test")
        result = carte({"page": produit_page}, carte_config)

        assert result["id"] == carte_config.slug
        assert "view_mode-view=liste" in result["url_variant"]
        # Control URL stays clean (no view_mode override).
        assert "view_mode-view=" not in result["url"]

    def test_ab_test_enabled_when_produit_page_opted_in(self, produit_page_ab_enabled):
        carte_config = CarteConfigFactory(slug="carte-ab-on")
        result = carte({"page": produit_page_ab_enabled}, carte_config)
        assert result["ab_test_enabled"] is True

    def test_ab_test_disabled_when_produit_page_not_opted_in(self, produit_page):
        # Default value of ab_test_carte_default_view is False — a ProduitPage
        # without the opt-in stays out of the experiment.
        carte_config = CarteConfigFactory(slug="carte-ab-off-page")
        result = carte({"page": produit_page}, carte_config)
        assert result["ab_test_enabled"] is False

    def test_ab_test_disabled_when_page_is_not_produit_page(self):
        carte_config = CarteConfigFactory(slug="carte-ab-off-other")
        # A plain object that exposes `sous_categorie_objet.all().values_list(...)`
        # but is not a ProduitPage instance.
        fake_page = MagicMock()
        fake_page.sous_categorie_objet.all.return_value.values_list.return_value = []
        result = carte({"page": fake_page}, carte_config)
        assert result["ab_test_enabled"] is False

    def test_url_variant_replaces_existing_view_mode_param(self, produit_page):
        carte_config = CarteConfigFactory(
            slug="carte-replace",
            SOLUTION_TEMPORAIRE_A_SUPPRIMER_DES_QUE_POSSIBLE_parametres_url=(
                "view_mode-view=carte&other=1"
            ),
        )
        result = carte({"page": produit_page}, carte_config)
        # Replaced, not duplicated.
        assert result["url_variant"].count("view_mode-view=") == 1
        assert "view_mode-view=liste" in result["url_variant"]
        assert "other=1" in result["url_variant"]
