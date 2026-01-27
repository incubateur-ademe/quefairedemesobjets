# flake8: noqa: E501
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from wagtail.models import Page, Site

from qfdmd.models import ProduitIndexPage, ProduitPage
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory


@pytest.fixture
def wagtail_site():
    """Ensure a default Wagtail site exists."""
    root_page = Page.objects.get(depth=1)
    site, _ = Site.objects.get_or_create(
        hostname="testserver",
        defaults={
            "root_page": root_page,
            "is_default_site": True,
            "site_name": "Test Site",
        },
    )
    return site


@pytest.fixture
def home_page(wagtail_site):
    """Get or create a home page (depth=2) for Wagtail with SEO fields."""
    # Get existing page at depth 2 or create one
    existing = Page.objects.filter(depth=2).first()
    if existing:
        # Update the existing page with SEO fields
        existing.seo_title = "Que faire de mes objets - Accueil"
        existing.search_description = "Description SEO de la page d'accueil"
        existing.save()
        return existing

    # If no page exists at depth 2, create one
    root_page = wagtail_site.root_page
    page = Page(
        title="Accueil",
        slug="accueil",
        seo_title="Que faire de mes objets - Accueil",
        search_description="Description SEO de la page d'accueil",
    )
    root_page.add_child(instance=page)
    page.save()
    return page


@pytest.fixture
def produit_index_page(wagtail_site):
    """Create a ProduitIndexPage."""
    root_page = wagtail_site.root_page
    # Check if it already exists
    existing = ProduitIndexPage.objects.filter(slug="produits-test").first()
    if existing:
        return existing

    page = ProduitIndexPage(
        title="Produits Test",
        slug="produits-test",
    )
    root_page.add_child(instance=page)
    page.save()
    return page


@pytest.fixture
def produit_page(produit_index_page):
    """Create a ProduitPage with SEO fields."""
    # Check if it already exists
    existing = ProduitPage.objects.filter(slug="bouteille-verre-test").first()
    if existing:
        existing.seo_title = "Que faire d'une bouteille en verre"
        existing.search_description = (
            "Découvrez comment recycler votre bouteille en verre"
        )
        existing.save()
        return existing

    page = ProduitPage(
        title="Ma bouteille en verre",
        slug="bouteille-verre-test",
        seo_title="Que faire d'une bouteille en verre",
        search_description="Découvrez comment recycler votre bouteille en verre",
    )
    produit_index_page.add_child(instance=page)
    page.save()
    return page


@pytest.mark.django_db
class TestHomepageSeoMetaTags:
    """Test SEO meta tags on the homepage."""

    def test_homepage_has_title_meta_tag(self, client, home_page):
        """Test that homepage has correct title tag."""
        with patch("qfdmd.views.get_homepage", return_value=home_page):
            response = client.get("/")

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.find("title")
        assert title is not None
        assert home_page.seo_title in title.text

    def test_homepage_has_description_meta_tag(self, client, home_page):
        """Test that homepage has correct description meta tag."""
        with patch("qfdmd.views.get_homepage", return_value=home_page):
            response = client.get("/")

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        description = soup.find("meta", attrs={"name": "description"})
        assert description is not None
        assert description["content"] == home_page.search_description

    def test_homepage_has_og_meta_tags(self, client, home_page):
        """Test that homepage has Open Graph meta tags."""
        with patch("qfdmd.views.get_homepage", return_value=home_page):
            response = client.get("/")

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

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

    def test_homepage_has_twitter_meta_tags(self, client, home_page):
        """Test that homepage has Twitter meta tags."""
        with patch("qfdmd.views.get_homepage", return_value=home_page):
            response = client.get("/")

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        assert twitter_title is not None
        assert home_page.seo_title in twitter_title["content"]

        twitter_description = soup.find("meta", attrs={"name": "twitter:description"})
        assert twitter_description is not None
        assert twitter_description["content"] == home_page.search_description


@pytest.mark.django_db
class TestLegacyProduitSeoMetaTags:
    """Test SEO meta tags on legacy produit pages (using Synonyme/object)."""

    def test_legacy_produit_has_title_meta_tag(self, client):
        """Test that legacy produit page has correct title tag."""
        produit = ProduitFactory(nom="Bouteille plastique")
        synonyme = SynonymeFactory(
            produit=produit,
            nom="Bouteille plastique",
            meta_description="Comment recycler une bouteille plastique",
        )

        response = client.get(synonyme.get_absolute_url())

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.find("title")
        assert title is not None
        assert synonyme.nom in title.text

    def test_legacy_produit_has_description_meta_tag(self, client):
        """Test that legacy produit page has correct description meta tag."""
        produit = ProduitFactory(nom="Bouteille plastique")
        synonyme = SynonymeFactory(
            produit=produit,
            nom="Bouteille plastique",
            meta_description="Comment recycler une bouteille plastique",
        )

        response = client.get(synonyme.get_absolute_url())

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        description = soup.find("meta", attrs={"name": "description"})
        assert description is not None
        assert description["content"] == synonyme.meta_description

    def test_legacy_produit_has_og_meta_tags(self, client):
        """Test that legacy produit page has Open Graph meta tags."""
        produit = ProduitFactory(nom="Bouteille plastique")
        synonyme = SynonymeFactory(
            produit=produit,
            nom="Bouteille plastique",
            meta_description="Comment recycler une bouteille plastique",
        )

        response = client.get(synonyme.get_absolute_url())

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        og_title = soup.find("meta", attrs={"property": "og:title"})
        assert og_title is not None
        assert synonyme.nom in og_title["content"]

        og_description = soup.find("meta", attrs={"property": "og:description"})
        assert og_description is not None
        assert og_description["content"] == synonyme.meta_description

        og_image = soup.find("meta", attrs={"property": "og:image"})
        assert og_image is not None

    def test_legacy_produit_has_twitter_meta_tags(self, client):
        """Test that legacy produit page has Twitter meta tags."""
        produit = ProduitFactory(nom="Bouteille plastique")
        synonyme = SynonymeFactory(
            produit=produit,
            nom="Bouteille plastique",
            meta_description="Comment recycler une bouteille plastique",
        )

        response = client.get(synonyme.get_absolute_url())

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        assert twitter_title is not None
        assert synonyme.nom in twitter_title["content"]

        twitter_description = soup.find("meta", attrs={"name": "twitter:description"})
        assert twitter_description is not None
        assert twitter_description["content"] == synonyme.meta_description


@pytest.mark.django_db
class TestProduitPageSeoMetaTags:
    """Test SEO meta tags on ProduitPage (Wagtail pages)."""

    def test_produit_page_has_title_meta_tag(self, client, produit_page):
        """Test that ProduitPage has correct title tag."""
        response = client.get(produit_page.url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.find("title")
        assert title is not None
        assert produit_page.seo_title in title.text

    def test_produit_page_has_description_meta_tag(self, client, produit_page):
        """Test that ProduitPage has correct description meta tag."""
        response = client.get(produit_page.url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        description = soup.find("meta", attrs={"name": "description"})
        assert description is not None
        assert description["content"] == produit_page.search_description

    def test_produit_page_has_og_meta_tags(self, client, produit_page):
        """Test that ProduitPage has Open Graph meta tags."""
        response = client.get(produit_page.url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

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

    def test_produit_page_has_twitter_meta_tags(self, client, produit_page):
        """Test that ProduitPage has Twitter meta tags."""
        response = client.get(produit_page.url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        assert twitter_title is not None
        assert produit_page.seo_title in twitter_title["content"]

        twitter_description = soup.find("meta", attrs={"name": "twitter:description"})
        assert twitter_description is not None
        assert twitter_description["content"] == produit_page.search_description

    def test_produit_page_falls_back_to_title_when_no_seo_title(
        self, client, produit_index_page
    ):
        """Test that ProduitPage falls back to title when seo_title is empty."""
        page = ProduitPage(
            title="Bouteille sans SEO title",
            slug="bouteille-sans-seo",
            search_description="Une description",
        )
        produit_index_page.add_child(instance=page)
        page.save()

        response = client.get(page.url)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.find("title")
        assert title is not None
        assert page.title in title.text

        og_title = soup.find("meta", attrs={"property": "og:title"})
        assert og_title is not None
        assert page.title in og_title["content"]
