import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from wagtail.models import Page, Site

from qfdmd.models import (
    LegacyIntermediateProduitPage,
    LegacyIntermediateProduitPageSynonymeExclusion,
    LegacyIntermediateSynonymePage,
    ProduitIndexPage,
    ProduitPage,
    SearchTag,
    Synonyme,
    TaggedSearchTag,
)
from qfdmd.views import import_legacy_synonymes
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory


@pytest.fixture
def wagtail_site():
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
    return wagtail_site.root_page


@pytest.fixture
def produit_index_page(root_page):
    page = ProduitIndexPage(title="Produits", slug="produits")
    root_page.add_child(instance=page)
    page.save()
    return page


@pytest.fixture
def produit_page(produit_index_page):
    page = ProduitPage(title="Produit Page", slug="produit-page")
    produit_index_page.add_child(instance=page)
    page.save()
    return page


def _make_request(method="get"):
    factory = RequestFactory()
    if method == "post":
        request = factory.post("/")
    else:
        request = factory.get("/")
    request.session = SessionStore()
    request.user, _ = User.objects.get_or_create(username="testuser")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


@pytest.mark.django_db
class TestImportLegacySynonymesView:
    def test_creates_search_tag_from_synonyme(self, produit_page):
        """Import creates a SearchTag with the lowercased synonyme name."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page, synonyme=synonyme
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        assert SearchTag.objects.filter(name="lave-linge").exists()

    def test_stores_legacy_reference_on_search_tag(self, produit_page):
        """Import stores the legacy synonyme reference on the SearchTag."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page, synonyme=synonyme
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        tag = SearchTag.objects.get(name="lave-linge")
        assert tag.legacy_existing_synonyme == synonyme

    def test_adds_search_tag_to_produit_page(self, produit_page):
        """Import adds the SearchTag to the ProduitPage."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page, synonyme=synonyme
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        tag = SearchTag.objects.get(name="lave-linge")
        assert TaggedSearchTag.objects.filter(
            tag=tag, content_object=produit_page
        ).exists()

    def test_reuses_existing_search_tag(self, produit_page):
        """Import reuses an existing SearchTag with the same lowercased name."""
        existing_tag = SearchTag.objects.create(name="lave-linge", slug="lave-linge")

        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page, synonyme=synonyme
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        assert SearchTag.objects.filter(name="lave-linge").count() == 1
        existing_tag.refresh_from_db()
        assert existing_tag.legacy_existing_synonyme == synonyme

    def test_imports_synonymes_from_produit_redirection(self, produit_page):
        """Import collects synonymes from products linked to the page."""
        produit = ProduitFactory(nom="Produit Redirection Test")
        SynonymeFactory(nom="Lave-Vaisselle Redirection", produit=produit)
        LegacyIntermediateProduitPage.objects.create(page=produit_page, produit=produit)

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        assert SearchTag.objects.filter(name="lave-vaisselle redirection").exists()
        tag = SearchTag.objects.get(name="lave-vaisselle redirection")
        assert TaggedSearchTag.objects.filter(
            tag=tag, content_object=produit_page
        ).exists()

    def test_does_not_import_product_synonyme_already_assigned_to_another_page(
        self, produit_index_page, produit_page
    ):
        """A synonyme collected via a produit must not be imported if it is already
        directly assigned (via next_wagtail_page) to a different page."""
        # page_a already owns "aspirateur" as a direct synonyme
        page_a = ProduitPage(title="Page A", slug="page-a")
        produit_index_page.add_child(instance=page_a)
        page_a.save()

        produit = ProduitFactory(nom="Petit electromenager")
        synonyme_aspirateur = SynonymeFactory(nom="Aspirateur", produit=produit)
        LegacyIntermediateSynonymePage.objects.create(
            page=page_a, synonyme=synonyme_aspirateur
        )

        # page_b (produit_page) is linked to the same produit
        LegacyIntermediateProduitPage.objects.create(page=produit_page, produit=produit)

        # Migrate page_b — "aspirateur" must NOT be collected
        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        assert not SearchTag.objects.filter(name="aspirateur").exists()

    def test_excludes_synonymes_marked_for_exclusion(self, produit_page):
        """Import skips synonymes that are in the exclusion list."""
        produit = ProduitFactory(nom="Produit Test")
        SynonymeFactory(nom="Inclus", produit=produit)
        synonyme_excluded = SynonymeFactory(nom="Exclu", produit=produit)
        LegacyIntermediateProduitPage.objects.create(page=produit_page, produit=produit)
        LegacyIntermediateProduitPageSynonymeExclusion.objects.create(
            page=produit_page, synonyme=synonyme_excluded
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        assert SearchTag.objects.filter(name="inclus").exists()
        assert not SearchTag.objects.filter(name="exclu").exists()

    def test_does_not_overwrite_existing_legacy_reference(self, produit_page):
        """If a SearchTag already has a legacy_existing_synonyme, don't overwrite it."""
        produit = ProduitFactory(nom="Produit Test")
        first_synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        second_synonyme = SynonymeFactory(nom="lave-linge", produit=produit)

        existing_tag = SearchTag.objects.create(
            name="lave-linge",
            slug="lave-linge",
            legacy_existing_synonyme=first_synonyme,
        )

        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page, synonyme=second_synonyme
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        existing_tag.refresh_from_db()
        assert existing_tag.legacy_existing_synonyme == first_synonyme

    def test_success_message(self, produit_page):
        """Import shows a success message with the count of imported synonymes."""
        produit = ProduitFactory(nom="Produit Test")
        SynonymeFactory(nom="Syn1", produit=produit)
        SynonymeFactory(nom="Syn2", produit=produit)
        LegacyIntermediateProduitPage.objects.create(page=produit_page, produit=produit)

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "2 synonyme(s)" in str(messages[0])

    def test_info_message_when_no_synonymes(self, produit_page):
        """Import shows an info message when there are no synonymes to import."""
        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "Aucun nouveau synonyme" in str(messages[0])


@pytest.mark.django_db
class TestImportConfirmationPage:
    """GET shows a confirmation page, POST executes the import."""

    def test_get_returns_confirmation_page(self, produit_page):
        """GET request renders the confirmation template."""
        produit = ProduitFactory(nom="Produit Test")
        SynonymeFactory(nom="Lave-Linge", produit=produit)
        LegacyIntermediateProduitPage.objects.create(page=produit_page, produit=produit)

        request = _make_request("get")
        response = import_legacy_synonymes(request, produit_page.id)

        assert response.status_code == 200

    def test_get_does_not_execute_import(self, produit_page):
        """GET request does not create SearchTags."""
        produit = ProduitFactory(nom="Produit Test")
        SynonymeFactory(nom="Lave-Linge", produit=produit)
        LegacyIntermediateProduitPage.objects.create(page=produit_page, produit=produit)

        request = _make_request("get")
        import_legacy_synonymes(request, produit_page.id)

        assert not SearchTag.objects.filter(name="lave-linge").exists()

    def test_get_blocked_when_already_migrated(self, produit_page):
        """GET redirects with warning if migration already done."""
        produit_page.migree_depuis_synonymes_legacy = True
        produit_page.save(update_fields=["migree_depuis_synonymes_legacy"])

        request = _make_request("get")
        response = import_legacy_synonymes(request, produit_page.id)

        assert response.status_code == 302
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "déjà été effectuée" in str(messages[0])

    def test_post_blocked_when_already_migrated(self, produit_page):
        """POST redirects with warning if migration already done."""
        produit_page.migree_depuis_synonymes_legacy = True
        produit_page.save(update_fields=["migree_depuis_synonymes_legacy"])

        request = _make_request("post")
        response = import_legacy_synonymes(request, produit_page.id)

        assert response.status_code == 302
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "déjà été effectuée" in str(messages[0])


@pytest.mark.django_db
class TestImportSetsImportedAsSearchTag:
    """Import sets imported_as_search_tag on the Synonyme."""

    def test_sets_imported_as_search_tag_on_synonyme(self, produit_page):
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page, synonyme=synonyme
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        synonyme.refresh_from_db()
        tag = SearchTag.objects.get(name="lave-linge")
        assert synonyme.imported_as_search_tag == tag

    def test_does_not_overwrite_existing_imported_as_search_tag(self, produit_page):
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)

        existing_tag = SearchTag.objects.create(name="other-tag", slug="other-tag")
        synonyme.imported_as_search_tag = existing_tag
        synonyme.save(update_fields=["imported_as_search_tag"])

        LegacyIntermediateSynonymePage.objects.create(
            page=produit_page, synonyme=synonyme
        )

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        synonyme.refresh_from_db()
        assert synonyme.imported_as_search_tag == existing_tag


@pytest.mark.django_db
class TestImportSetsMigrationFlag:
    """Import sets migree_depuis_synonymes_legacy to True."""

    def test_sets_flag_after_import(self, produit_page):
        produit = ProduitFactory(nom="Produit Test")
        SynonymeFactory(nom="Syn1", produit=produit)
        LegacyIntermediateProduitPage.objects.create(page=produit_page, produit=produit)

        assert not produit_page.migree_depuis_synonymes_legacy

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        produit_page.refresh_from_db()
        assert produit_page.migree_depuis_synonymes_legacy

    def test_sets_flag_even_with_no_synonymes(self, produit_page):
        assert not produit_page.migree_depuis_synonymes_legacy

        request = _make_request("post")
        import_legacy_synonymes(request, produit_page.id)

        produit_page.refresh_from_db()
        assert produit_page.migree_depuis_synonymes_legacy


@pytest.mark.django_db
class TestSearchTagLowercaseOnSave:
    def test_name_is_lowercased_on_create(self):
        tag = SearchTag.objects.create(name="Réfrigérateur", slug="refrigerateur")
        assert tag.name == "réfrigérateur"

    def test_name_is_lowercased_on_update(self):
        tag = SearchTag.objects.create(name="frigo", slug="frigo")
        tag.name = "FRIGO"
        tag.save()
        tag.refresh_from_db()
        assert tag.name == "frigo"


@pytest.mark.django_db
class TestSynonymeIndexExclusion:
    """Synonymes with a SearchTag linked to a ProduitPage are excluded from index."""

    def test_synonyme_excluded_when_imported_as_search_tag_linked_to_page(
        self, produit_page
    ):
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        tag = SearchTag.objects.create(
            name="lave-linge",
            slug="lave-linge",
            legacy_existing_synonyme=synonyme,
        )
        TaggedSearchTag.objects.create(tag=tag, content_object=produit_page)
        synonyme.imported_as_search_tag = tag
        synonyme.save(update_fields=["imported_as_search_tag"])

        indexed = Synonyme.get_indexed_objects()
        assert synonyme not in indexed

    def test_synonyme_excluded_when_imported_as_search_tag_set(self):
        """Synonyme with imported_as_search_tag set is excluded from index."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        tag = SearchTag.objects.create(name="lave-linge", slug="lave-linge")
        synonyme.imported_as_search_tag = tag
        synonyme.save(update_fields=["imported_as_search_tag"])

        indexed = Synonyme.get_indexed_objects()
        assert synonyme not in indexed

    def test_synonyme_not_excluded_when_imported_as_search_tag_null(self):
        """Synonyme without imported_as_search_tag remains in index."""
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)

        indexed = Synonyme.get_indexed_objects()
        assert synonyme in indexed

    def test_synonyme_not_excluded_when_search_tag_has_no_page(self):
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        SearchTag.objects.create(
            name="lave-linge",
            slug="lave-linge",
            legacy_existing_synonyme=synonyme,
        )

        indexed = Synonyme.get_indexed_objects()
        assert synonyme in indexed

    def test_synonyme_not_excluded_when_no_search_tag(self):
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)

        indexed = Synonyme.get_indexed_objects()
        assert synonyme in indexed


@pytest.mark.django_db
class TestTaggedSearchTagDeleteReindex:
    """Deleting a TaggedSearchTag re-indexes the legacy synonyme if orphaned."""

    def test_synonyme_reindexable_after_tag_unlinked(self, produit_page):
        produit = ProduitFactory(nom="Produit Test")
        synonyme = SynonymeFactory(nom="Lave-Linge", produit=produit)
        tag = SearchTag.objects.create(
            name="lave-linge",
            slug="lave-linge",
            legacy_existing_synonyme=synonyme,
        )
        synonyme.imported_as_search_tag = tag
        synonyme.save(update_fields=["imported_as_search_tag"])
        tagged = TaggedSearchTag.objects.create(tag=tag, content_object=produit_page)

        # Synonyme excluded while linked
        assert synonyme not in Synonyme.get_indexed_objects()

        # Delete the link — synonyme stays excluded because
        # imported_as_search_tag is still set
        tagged.delete()
        synonyme.refresh_from_db()
        assert synonyme not in Synonyme.get_indexed_objects()

        # Clearing imported_as_search_tag brings the synonyme back
        synonyme.imported_as_search_tag = None
        synonyme.save(update_fields=["imported_as_search_tag"])
        assert synonyme in Synonyme.get_indexed_objects()

    def test_no_error_when_tag_has_no_legacy_synonyme(self, produit_page):
        tag = SearchTag.objects.create(name="frigo", slug="frigo")
        tagged = TaggedSearchTag.objects.create(tag=tag, content_object=produit_page)

        # Should not raise
        tagged.delete()
        assert not TaggedSearchTag.objects.filter(tag=tag).exists()


@pytest.mark.django_db
class TestSearchTagIndexExclusion:
    """Orphaned SearchTags (no linked ProduitPage) are excluded from the index."""

    def test_search_tag_indexed_when_linked_to_page(self, produit_page):
        tag = SearchTag.objects.create(name="frigo", slug="frigo")
        TaggedSearchTag.objects.create(tag=tag, content_object=produit_page)

        indexed = SearchTag.get_indexed_objects()
        assert tag in indexed

    def test_search_tag_excluded_when_no_page(self):
        tag = SearchTag.objects.create(name="frigo", slug="frigo")

        indexed = SearchTag.get_indexed_objects()
        assert tag not in indexed

    def test_search_tag_excluded_after_unlinked_from_page(self, produit_page):
        tag = SearchTag.objects.create(name="frigo", slug="frigo")
        tagged = TaggedSearchTag.objects.create(tag=tag, content_object=produit_page)

        assert tag in SearchTag.get_indexed_objects()

        tagged.delete()

        assert tag not in SearchTag.get_indexed_objects()
