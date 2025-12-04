import pytest
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from wagtail.models import Page, Site

from qfdmd.models import (
    LegacyIntermediateProduitPage,
    LegacyIntermediateProduitPageSynonymeExclusion,
    LegacyIntermediateSynonymePage,
    ProduitIndexPage,
    ProduitPage,
)
from qfdmd.views import SynonymeDetailView
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory


@pytest.fixture
def wagtail_site():
    """Ensure a default Wagtail site exists."""
    root_page = Page.objects.get(depth=1)
    site, _ = Site.objects.get_or_create(
        hostname="localhost",
        defaults={
            "root_page": root_page,
            "is_default_site": True,
            "site_name": "Test Site",
        },
    )
    return site


@pytest.fixture
def root_page(wagtail_site):
    """Create a root page for Wagtail."""
    return wagtail_site.root_page


@pytest.fixture
def produit_index_page(root_page):
    """Create a ProduitIndexPage."""
    page = ProduitIndexPage(
        title="Produits",
        slug="produits",
    )
    root_page.add_child(instance=page)
    page.save()
    return page


@pytest.fixture
def produit_page_a(produit_index_page):
    """Create a ProduitPage A."""
    page = ProduitPage(
        title="Produit Page A",
        slug="produit-page-a",
    )
    produit_index_page.add_child(instance=page)
    page.save()
    return page


@pytest.fixture
def produit_page_b(produit_index_page):
    """Create a ProduitPage B."""
    page = ProduitPage(
        title="Produit Page B",
        slug="produit-page-b",
    )
    produit_index_page.add_child(instance=page)
    page.save()
    return page


@pytest.mark.django_db
class TestLegacyIntermediateSynonymePage:
    """Test LegacyIntermediateSynonymePage model validation."""

    def test_create_direct_synonyme_redirection(self, produit_page_a, db):
        """Test creating a direct synonyme redirection."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create the intermediate relation
        intermediate = LegacyIntermediateSynonymePage(
            page=produit_page_a,
            synonyme=synonyme,
        )
        intermediate.clean()  # Should not raise
        intermediate.save()

        # Verify the relation exists
        assert synonyme.next_wagtail_page.page == produit_page_a

    def test_conflict_with_exclusion_raises_error(
        self, produit_page_a, produit_page_b, db
    ):
        """Test that creating a direct redirection for an excluded
        synonyme raises ValidationError."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create an exclusion first
        exclusion = LegacyIntermediateProduitPageSynonymeExclusion(
            page=produit_page_b,
            synonyme=synonyme,
        )
        exclusion.save()

        # Try to create a direct redirection
        intermediate = LegacyIntermediateSynonymePage(
            page=produit_page_a,
            synonyme=synonyme,
        )

        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            intermediate.clean()

        assert "Conflit" in str(exc_info.value)
        assert produit_page_b.title in str(exc_info.value)


@pytest.mark.django_db
class TestLegacyIntermediateProduitPageSynonymeExclusion:
    """Test LegacyIntermediateProduitPageSynonymeExclusion validation."""

    def test_exclude_synonyme_without_direct_redirection(self, produit_page_a, db):
        """Test excluding a synonyme that has no direct redirection."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create the exclusion
        exclusion = LegacyIntermediateProduitPageSynonymeExclusion(
            page=produit_page_a,
            synonyme=synonyme,
        )
        exclusion.clean()  # Should not raise
        exclusion.save()

        # Verify the exclusion exists
        assert synonyme.should_not_redirect_to.page == produit_page_a

    def test_exclude_synonyme_with_direct_redirection_raises_error(
        self, produit_page_a, produit_page_b, db
    ):
        """Test that excluding a synonyme with a direct redirection
        raises ValidationError."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create a direct redirection first
        intermediate = LegacyIntermediateSynonymePage(
            page=produit_page_b,
            synonyme=synonyme,
        )
        intermediate.save()

        # Try to create an exclusion
        exclusion = LegacyIntermediateProduitPageSynonymeExclusion(
            page=produit_page_a,
            synonyme=synonyme,
        )

        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            exclusion.clean()

        assert "Conflit" in str(exc_info.value)
        assert produit_page_b.title in str(exc_info.value)


@pytest.mark.django_db
class TestSynonymeDetailViewRedirection:
    """Test SynonymeDetailView redirection priority."""

    def test_direct_synonyme_redirection_takes_priority(
        self, produit_page_a, produit_page_b, db, settings
    ):
        """Test that direct synonyme redirection takes priority over
        produit redirection."""

        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create produit redirection to page A
        LegacyIntermediateProduitPage.objects.create(
            page=produit_page_a,
            produit=produit,
        )

        # Create direct synonyme redirection to page B
        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page_b,
            synonyme=synonyme,
        )

        # Create a request
        factory = RequestFactory()
        request = factory.get(f"/produit/{synonyme.slug}/")
        request.beta = True

        # Create view and get response
        view = SynonymeDetailView()
        view.setup(request, slug=synonyme.slug)
        response = view.get(request, slug=synonyme.slug)

        # Should redirect to page B (direct synonyme redirection)
        assert response.status_code == 302
        assert response.url == produit_page_b.url

    def test_produit_redirection_when_no_direct_synonyme(
        self, produit_page_a, db, settings
    ):
        """Test that produit redirection works when synonyme has no
        direct redirection."""

        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create only produit redirection
        LegacyIntermediateProduitPage.objects.create(
            page=produit_page_a,
            produit=produit,
        )

        # Create a request
        factory = RequestFactory()
        request = factory.get(f"/produit/{synonyme.slug}/")
        request.beta = True

        # Create view and get response
        view = SynonymeDetailView()
        view.setup(request, slug=synonyme.slug)
        response = view.get(request, slug=synonyme.slug)

        # Should redirect to page A (produit redirection)
        assert response.status_code == 302
        assert response.url == produit_page_a.url

    def test_exclusion_blocks_produit_redirection(self, produit_page_a, db, settings):
        """Test that exclusion prevents produit redirection."""

        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create produit redirection
        LegacyIntermediateProduitPage.objects.create(
            page=produit_page_a,
            produit=produit,
        )

        # Create exclusion for this synonyme
        LegacyIntermediateProduitPageSynonymeExclusion.objects.create(
            page=produit_page_a,
            synonyme=synonyme,
        )

        # Create a request
        factory = RequestFactory()
        request = factory.get(f"/produit/{synonyme.slug}/")
        request.beta = True

        # Create view and get response
        view = SynonymeDetailView()
        view.setup(request, slug=synonyme.slug)
        response = view.get(request, slug=synonyme.slug)

        # Should NOT redirect (exclusion blocks it)
        assert response.status_code == 200

        synonyme = SynonymeFactory(nom="Synonyme Test", produit=produit)

        # Create direct synonyme redirection
        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page_a,
            synonyme=synonyme,
        )

        # Create a request without beta
        factory = RequestFactory()
        request = factory.get(f"/produit/{synonyme.slug}/")
        request.beta = False

        # Create view and get response
        view = SynonymeDetailView()
        view.setup(request, slug=synonyme.slug)
        response = view.get(request, slug=synonyme.slug)

        # Should NOT redirect
        assert response.status_code == 200
