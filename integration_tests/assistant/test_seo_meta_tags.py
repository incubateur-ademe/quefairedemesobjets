from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from wagtail.models import Page, Site

from unit_tests.qfdmd.qfdmod_factory import (
    PageFactory,
    ProduitFactory,
    ProduitIndexPageFactory,
    ProduitPageFactory,
    SynonymeFactory,
)


@pytest.fixture
def wagtail_site():
    """Ensure a default Wagtail site exists with testserver hostname."""
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


@pytest.mark.django_db
class TestHomepageSeoMetaTags:
    """Test SEO meta tags on the homepage."""

    def test_homepage_has_seo_meta_tags(self, client):
        """Test that homepage has all required SEO meta tags."""
        root_page = Page.objects.get(depth=1)
        home_page = PageFactory(
            parent=root_page,
            title="Accueil",
            seo_title="Que faire de mes objets - Accueil",
            search_description="Description SEO de la page d'accueil",
        )

        with patch("qfdmd.views.get_homepage", return_value=home_page):
            response = client.get("/")

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        # Title
        title = soup.find("title")
        assert title is not None
        assert home_page.seo_title in title.text

        # Description
        description = soup.find("meta", attrs={"name": "description"})
        assert description is not None
        assert description["content"] == home_page.search_description

        # Open Graph tags
        og_title = soup.find("meta", attrs={"property": "og:title"})
        assert og_title is not None
        assert home_page.seo_title in og_title["content"]

        og_description = soup.find("meta", attrs={"property": "og:description"})
        assert og_description is not None
        assert og_description["content"] == home_page.search_description

        og_type = soup.find("meta", attrs={"property": "og:type"})
        assert og_type is not None
        assert og_type["content"] == "article"

        og_image = soup.find("meta", attrs={"property": "og:image"})
        assert og_image is not None

        # Twitter tags
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        assert twitter_title is not None
        assert home_page.seo_title in twitter_title["content"]

        twitter_description = soup.find("meta", attrs={"name": "twitter:description"})
        assert twitter_description is not None
        assert twitter_description["content"] == home_page.search_description


@pytest.mark.django_db
class TestLegacyProduitSeoMetaTags:
    """Test SEO meta tags on legacy produit pages (using Synonyme/object)."""

    def test_legacy_produit_has_seo_meta_tags(self, client):
        """Test that legacy produit page has all required SEO meta tags."""
        produit = ProduitFactory(nom="Bouteille plastique")
        synonyme = SynonymeFactory(
            produit=produit,
            nom="Bouteille plastique",
            meta_description="Comment recycler une bouteille plastique",
        )

        response = client.get(synonyme.get_absolute_url())

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        # Title
        title = soup.find("title")
        assert title is not None
        assert synonyme.nom in title.text

        # Description
        description = soup.find("meta", attrs={"name": "description"})
        assert description is not None
        assert description["content"] == synonyme.meta_description

        # Open Graph tags
        og_title = soup.find("meta", attrs={"property": "og:title"})
        assert og_title is not None
        assert synonyme.nom in og_title["content"]

        og_description = soup.find("meta", attrs={"property": "og:description"})
        assert og_description is not None
        assert og_description["content"] == synonyme.meta_description

        og_image = soup.find("meta", attrs={"property": "og:image"})
        assert og_image is not None

        # Twitter tags
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        assert twitter_title is not None
        assert synonyme.nom in twitter_title["content"]

        twitter_description = soup.find("meta", attrs={"name": "twitter:description"})
        assert twitter_description is not None
        assert twitter_description["content"] == synonyme.meta_description


@pytest.mark.django_db
class TestProduitPageSeoMetaTags:
    """Test SEO meta tags on ProduitPage (Wagtail pages)."""

    def test_produit_page_has_seo_meta_tags(self, client, wagtail_site):
        """Test that ProduitPage has all required SEO meta tags."""
        root_page = wagtail_site.root_page
        produit_index = ProduitIndexPageFactory(parent=root_page)
        produit_page = ProduitPageFactory(
            parent=produit_index,
            title="Ma bouteille en verre",
            seo_title="Que faire d'une bouteille en verre",
            search_description="Découvrez comment recycler votre bouteille en verre",
        )

        response = client.get(produit_page.url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        # Title
        title = soup.find("title")
        assert title is not None
        assert produit_page.seo_title in title.text

        # Description
        description = soup.find("meta", attrs={"name": "description"})
        assert description is not None
        assert description["content"] == produit_page.search_description

        # Open Graph tags
        og_title = soup.find("meta", attrs={"property": "og:title"})
        assert og_title is not None
        assert produit_page.seo_title in og_title["content"]

        og_description = soup.find("meta", attrs={"property": "og:description"})
        assert og_description is not None
        assert og_description["content"] == produit_page.search_description

        og_type = soup.find("meta", attrs={"property": "og:type"})
        assert og_type is not None
        assert og_type["content"] == "article"

        og_image = soup.find("meta", attrs={"property": "og:image"})
        assert og_image is not None

        # Twitter tags
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        assert twitter_title is not None
        assert produit_page.seo_title in twitter_title["content"]

        twitter_description = soup.find("meta", attrs={"name": "twitter:description"})
        assert twitter_description is not None
        assert twitter_description["content"] == produit_page.search_description

    def test_produit_page_falls_back_to_title_when_no_seo_title(
        self, client, wagtail_site
    ):
        """Test that ProduitPage falls back to title when seo_title is empty."""
        root_page = wagtail_site.root_page
        produit_index = ProduitIndexPageFactory(parent=root_page)
        produit_page = ProduitPageFactory(
            parent=produit_index,
            title="Bouteille sans SEO title",
            seo_title="",
            search_description="Une description",
        )

        response = client.get(produit_page.url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        # Title should fall back to page.title
        title = soup.find("title")
        assert title is not None
        assert produit_page.title in title.text

        # og:title should also fall back
        og_title = soup.find("meta", attrs={"property": "og:title"})
        assert og_title is not None
        assert produit_page.title in og_title["content"]
