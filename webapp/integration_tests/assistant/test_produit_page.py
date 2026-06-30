import pytest
from bs4 import BeautifulSoup
from wagtail.models import Page, Site

from unit_tests.qfdmd.qfdmod_factory import (
    ProduitIndexPageFactory,
    ProduitPageFactory,
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
class TestProduitPageBodyClasses:
    """Test that ProduitPage renders with the produit-page body class."""

    def test_produit_page_has_produit_page_body_class(self, client, wagtail_site):
        """Test that ProduitPage includes body_classes block with produit-page class."""
        root_page = wagtail_site.root_page
        produit_index = ProduitIndexPageFactory(parent=root_page)
        produit_page = ProduitPageFactory(
            parent=produit_index,
            title="Ma bouteille en verre",
        )

        response = client.get(produit_page.url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        body = soup.find("body")
        assert body is not None
        body_classes = body.get("class", "")
        assert isinstance(body_classes, str) and "produit-page" in body_classes
