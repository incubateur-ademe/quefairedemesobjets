import pytest
from django.contrib.contenttypes.models import ContentType

from qfdmd.models import SearchTag, TaggedSearchTag
from search.models import SearchTerm
from unit_tests.qfdmd.qfdmod_factory import (
    ProduitFactory,
    ProduitPageFactory,
    SynonymeFactory,
)


class TestSearchTermModel:
    """Tests for the SearchTerm model itself."""

    @pytest.mark.django_db
    def test_str_returns_term(self):
        """SearchTerm __str__ should return the term field."""
        content_type = ContentType.objects.get_for_model(SearchTag)
        search_term = SearchTerm.objects.create(
            term="test term",
            linked_content_type=content_type,
            linked_object_id=99999,
        )
        assert str(search_term) == "test term"

    @pytest.mark.django_db
    def test_get_supported_content_types(self):
        """Should return ContentTypes for all supported models."""
        content_types = SearchTerm.get_supported_content_types()
        app_models = [(ct.app_label, ct.model) for ct in content_types]

        for app_label, model in SearchTerm.supported_content_types:
            assert (app_label, model) in app_models

    @pytest.mark.django_db
    def test_unique_together_constraint(self):
        """Should not allow duplicate SearchTerms for the same object."""
        content_type = ContentType.objects.get_for_model(SearchTag)
        SearchTerm.objects.create(
            term="term 1",
            linked_content_type=content_type,
            linked_object_id=99999,
        )

        with pytest.raises(Exception):
            SearchTerm.objects.create(
                term="term 2",
                linked_content_type=content_type,
                linked_object_id=99999,
            )


class TestSearchTermSyncFromObject:
    """Tests for SearchTerm.sync_from_object method."""

    @pytest.mark.django_db
    def test_sync_creates_search_term_for_synonyme(self):
        """Syncing a Synonyme should create a SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="Test Synonyme", produit=produit)

        search_term, created = SearchTerm.sync_from_object(synonyme)

        assert created is False  # Already created by save()
        assert search_term.term == "Test Synonyme"
        assert search_term.legacy is True

    @pytest.mark.django_db
    def test_sync_updates_existing_search_term(self):
        """Syncing an existing object should update the SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="Original Name", produit=produit)

        search_term1 = SearchTerm.objects.get(term="Original Name")

        # Update the synonyme name (without calling save to avoid auto-sync)
        from qfdmd.models import Synonyme

        Synonyme.objects.filter(pk=synonyme.pk).update(nom="Updated Name")
        synonyme.refresh_from_db()

        search_term2, created2 = SearchTerm.sync_from_object(synonyme)
        assert created2 is False
        assert search_term2.pk == search_term1.pk
        assert search_term2.term == "Updated Name"

    @pytest.mark.django_db
    def test_sync_sets_parent_object_when_available(self):
        """Syncing should set parent object when available."""
        # For Synonyme, parent_object is None (legacy)
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="Test Synonyme", produit=produit)

        search_term, _ = SearchTerm.sync_from_object(synonyme)

        # Synonyme returns None for parent_object
        assert search_term.parent_content_type is None
        assert search_term.parent_object_id is None


class TestSearchTermDeleteForObject:
    """Tests for SearchTerm.delete_for_object method."""

    @pytest.mark.django_db
    def test_delete_for_object_removes_search_term(self):
        """Deleting for an object should remove its SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="Test Synonyme", produit=produit)

        assert SearchTerm.objects.filter(term="Test Synonyme").exists()

        SearchTerm.delete_for_object(synonyme)
        assert not SearchTerm.objects.filter(term="Test Synonyme").exists()

    @pytest.mark.django_db
    def test_delete_for_object_handles_nonexistent_search_term(self):
        """Deleting for an object without a SearchTerm should not raise."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="Test Synonyme", produit=produit)

        # Delete the SearchTerm first
        SearchTerm.delete_for_object(synonyme)

        # Calling again should not raise
        SearchTerm.delete_for_object(synonyme)


class TestSynonymeSearchTermIntegration:
    """Tests for Synonyme <-> SearchTerm integration via SearchTermSyncMixin."""

    @pytest.mark.django_db
    def test_synonyme_save_creates_search_term(self):
        """Saving a Synonyme should automatically create a SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")

        # Count before
        initial_count = SearchTerm.objects.count()

        SynonymeFactory(nom="Auto Sync Test", produit=produit)

        # Count after
        assert SearchTerm.objects.count() == initial_count + 1
        search_term = SearchTerm.objects.get(term="Auto Sync Test")
        assert search_term.legacy is True

    @pytest.mark.django_db
    def test_synonyme_save_updates_search_term(self):
        """Updating a Synonyme should update its SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="Original", produit=produit)

        search_term = SearchTerm.objects.get(term="Original")
        original_pk = search_term.pk

        # Update the synonyme
        synonyme.nom = "Updated"
        synonyme.save()

        # Should update, not create new
        assert SearchTerm.objects.filter(pk=original_pk).exists()
        search_term.refresh_from_db()
        assert search_term.term == "Updated"

    @pytest.mark.django_db
    def test_synonyme_delete_removes_search_term(self):
        """Deleting a Synonyme should remove its SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="To Delete", produit=produit)

        assert SearchTerm.objects.filter(term="To Delete").exists()

        synonyme.delete()

        assert not SearchTerm.objects.filter(term="To Delete").exists()

    @pytest.mark.django_db
    def test_synonyme_url_is_synced(self):
        """Synonyme's URL should be synced to SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="URL Test", produit=produit)

        search_term = SearchTerm.objects.get(term="URL Test")
        expected_url = synonyme.get_absolute_url()
        assert search_term.url == expected_url


class TestSearchTagSearchTermIntegration:
    """Tests for SearchTag <-> SearchTerm integration."""

    @pytest.fixture
    def produit_page(self, db):
        """Create a ProduitPage for testing."""
        from wagtail.models import Page

        root = Page.objects.get(depth=1)
        from qfdmd.models import ProduitIndexPage

        index_page = ProduitIndexPage(title="Products", slug="products")
        root.add_child(instance=index_page)

        produit_page = ProduitPageFactory.build(title="Test Product", slug="test-prod")
        index_page.add_child(instance=produit_page)
        return produit_page

    @pytest.mark.django_db
    def test_search_tag_without_page_has_empty_url(self):
        """A SearchTag not linked to a page should have empty URL."""
        SearchTag.objects.create(name="Orphan Tag", slug="orphan-tag")

        # The mixin checks if the content type is supported, but SearchTag
        # is in the supported list. However, without a page, the URL will be empty.
        # Check that a SearchTerm was created (since it's in supported types)
        search_terms = SearchTerm.objects.filter(term="Orphan Tag")
        assert search_terms.exists()
        assert search_terms.first().url == ""

    @pytest.mark.django_db
    def test_tagged_search_tag_creates_search_term_with_url(self, produit_page):
        """Creating TaggedSearchTag should create SearchTerm with page URL."""
        search_tag = SearchTag.objects.create(name="Linked Tag", slug="linked-tag")

        # Initially, the search term has no URL
        search_term = SearchTerm.objects.get(term="Linked Tag")
        assert search_term.url == ""

        # Link the tag to the page
        TaggedSearchTag.objects.create(tag=search_tag, content_object=produit_page)

        # The SearchTerm should now have the page URL
        search_term.refresh_from_db()
        assert search_term.url == produit_page.url

    @pytest.mark.django_db
    def test_tagged_search_tag_delete_removes_search_term(self, produit_page):
        """Deleting TaggedSearchTag should remove the SearchTerm."""
        search_tag = SearchTag.objects.create(name="To Unlink", slug="to-unlink")
        tagged = TaggedSearchTag.objects.create(
            tag=search_tag, content_object=produit_page
        )

        assert SearchTerm.objects.filter(term="To Unlink").exists()

        # Delete the relationship
        tagged.delete()

        # SearchTerm should be removed
        assert not SearchTerm.objects.filter(term="To Unlink").exists()

    @pytest.mark.django_db
    def test_search_tag_delete_removes_search_term(self, produit_page):
        """Deleting a SearchTag should remove its SearchTerm."""
        search_tag = SearchTag.objects.create(name="Tag To Delete", slug="tag-delete")
        TaggedSearchTag.objects.create(tag=search_tag, content_object=produit_page)

        assert SearchTerm.objects.filter(term="Tag To Delete").exists()

        # Delete the tag itself
        search_tag.delete()

        # SearchTerm should be gone
        assert not SearchTerm.objects.filter(term="Tag To Delete").exists()

    @pytest.mark.django_db
    def test_search_tag_parent_object_is_produit_page(self, produit_page):
        """SearchTag's parent_object should be the linked ProduitPage."""
        search_tag = SearchTag.objects.create(name="Parent Test", slug="parent-test")
        TaggedSearchTag.objects.create(tag=search_tag, content_object=produit_page)

        search_term = SearchTerm.objects.get(term="Parent Test")

        assert search_term.parent_object == produit_page


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.django_db
    def test_sync_with_empty_term(self):
        """Syncing an object with empty term should still work."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="", produit=produit)

        search_term = SearchTerm.objects.get(linked_object_id=synonyme.pk)
        assert search_term.term == ""

    @pytest.mark.django_db
    def test_sync_with_very_long_term(self):
        """Syncing with a term at max length should work."""
        produit = ProduitFactory(nom="Test Produit")
        long_name = "X" * 255
        synonyme = SynonymeFactory(nom=long_name, produit=produit)

        search_term = SearchTerm.objects.get(linked_object_id=synonyme.pk)
        assert len(search_term.term) == 255

    @pytest.mark.django_db
    def test_multiple_synonymes_create_separate_search_terms(self):
        """Each Synonyme should have its own SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        SynonymeFactory(nom="Synonyme One", produit=produit)
        SynonymeFactory(nom="Synonyme Two", produit=produit)

        assert SearchTerm.objects.filter(term="Synonyme One").exists()
        assert SearchTerm.objects.filter(term="Synonyme Two").exists()

        # They should be different SearchTerms
        st1 = SearchTerm.objects.get(term="Synonyme One")
        st2 = SearchTerm.objects.get(term="Synonyme Two")
        assert st1.pk != st2.pk

    @pytest.mark.django_db
    def test_delete_nonexistent_object_is_safe(self):
        """Calling delete_for_object without SearchTerm should not raise."""
        produit = ProduitFactory(nom="Test Produit")
        synonyme = SynonymeFactory(nom="No Search Term", produit=produit)

        # Delete the SearchTerm first
        SearchTerm.delete_for_object(synonyme)

        # Calling again should not raise
        SearchTerm.delete_for_object(synonyme)

    @pytest.mark.django_db
    def test_search_term_legacy_flag_for_synonyme(self):
        """Synonyme should always have legacy=True on its SearchTerm."""
        produit = ProduitFactory(nom="Test Produit")
        SynonymeFactory(nom="Legacy Test", produit=produit)

        search_term = SearchTerm.objects.get(term="Legacy Test")
        assert search_term.legacy is True

    @pytest.fixture
    def produit_page_for_edge_cases(self, db):
        """Create a ProduitPage for edge case testing."""
        from wagtail.models import Page

        from qfdmd.models import ProduitIndexPage

        root = Page.objects.get(depth=1)
        index_page = ProduitIndexPage(title="Products Edge", slug="products-edge")
        root.add_child(instance=index_page)

        produit_page = ProduitPageFactory.build(title="Edge Product", slug="edge-prod")
        index_page.add_child(instance=produit_page)
        return produit_page

    @pytest.mark.django_db
    def test_search_tag_legacy_flag_is_false(self, produit_page_for_edge_cases):
        """SearchTag should have legacy=False on its SearchTerm."""
        search_tag = SearchTag.objects.create(name="Non Legacy", slug="non-legacy")
        TaggedSearchTag.objects.create(
            tag=search_tag, content_object=produit_page_for_edge_cases
        )

        search_term = SearchTerm.objects.get(term="Non Legacy")
        assert search_term.legacy is False
