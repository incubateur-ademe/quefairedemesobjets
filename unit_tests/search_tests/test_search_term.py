import pytest
from wagtail.models import Page

from qfdmd.models import (
    Produit,
    ProduitIndexPage,
    ProduitPage,
    ProduitPageSearchTerm,
    SearchTag,
    Synonyme,
    TaggedSearchTag,
)
from search.models import SearchTerm


@pytest.fixture
def produit():
    return Produit.objects.create(nom="Test Produit")


@pytest.fixture
def produit_page():
    root = Page.objects.get(depth=1)
    index_page = ProduitIndexPage(title="Products", slug="products")
    root.add_child(instance=index_page)
    page = ProduitPage(title="Test Product", slug="test-product")
    index_page.add_child(instance=page)
    return page


@pytest.mark.django_db
class TestSynonymeCreatesSearchTerm:
    def test_creating_synonyme_creates_search_term(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)

        assert SearchTerm.objects.filter(pk=synonyme.searchterm_ptr_id).exists()

    def test_updating_synonyme_preserves_search_term(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        original_ptr_id = synonyme.searchterm_ptr_id

        synonyme.nom = "Machine à laver"
        synonyme.save()
        synonyme.refresh_from_db()

        assert synonyme.searchterm_ptr_id == original_ptr_id
        assert SearchTerm.objects.filter(pk=original_ptr_id).exists()

    def test_deleting_synonyme_removes_search_term(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        ptr_id = synonyme.searchterm_ptr_id

        synonyme.delete()

        assert not SearchTerm.objects.filter(pk=ptr_id).exists()


@pytest.mark.django_db
class TestSearchTagCreatesSearchTerm:
    def test_creating_search_tag_creates_search_term(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")

        assert SearchTerm.objects.filter(pk=tag.searchterm_ptr_id).exists()

    def test_updating_search_tag_preserves_search_term(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        original_ptr_id = tag.searchterm_ptr_id

        tag.name = "frigo"
        tag.slug = "frigo"
        tag.save()
        tag.refresh_from_db()

        assert tag.searchterm_ptr_id == original_ptr_id
        assert SearchTerm.objects.filter(pk=original_ptr_id).exists()

    def test_deleting_search_tag_removes_search_term(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        ptr_id = tag.searchterm_ptr_id

        tag.delete()

        assert not SearchTerm.objects.filter(pk=ptr_id).exists()


@pytest.mark.django_db
class TestSearchTermSpecificResolution:
    def test_specific_returns_synonyme(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        search_term = SearchTerm.objects.get(pk=synonyme.searchterm_ptr_id)

        specific = search_term.specific
        assert isinstance(specific, Synonyme)
        assert specific.pk == synonyme.pk

    def test_specific_returns_search_tag(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        search_term = SearchTerm.objects.get(pk=tag.searchterm_ptr_id)

        specific = search_term.specific
        assert isinstance(specific, SearchTag)
        assert specific.pk == tag.pk

    def test_search_result_template_for_synonyme(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        search_term = SearchTerm.objects.get(pk=synonyme.searchterm_ptr_id)

        assert (
            search_term.specific.search_result_template
            == "ui/components/search/search_result_synonyme.html"
        )

    def test_search_result_template_for_search_tag(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        search_term = SearchTerm.objects.get(pk=tag.searchterm_ptr_id)

        assert (
            search_term.specific.search_result_template
            == "ui/components/search/search_result_searchtag.html"
        )

    def test_search_result_template_for_produit_page(self, produit_page):
        assert (
            produit_page.search_result_template
            == "ui/components/search/search_result_produitpage.html"
        )


@pytest.mark.django_db
class TestProduitPageSearchTermIndexExclusion:
    """ProduitPageSearchTerms linked to non-live pages are excluded from index."""

    def test_indexed_when_page_is_live(self, produit_page):
        search_term = produit_page.produit_page_search_term

        indexed = ProduitPageSearchTerm.get_indexed_objects()
        assert search_term in indexed

    def test_excluded_when_page_is_not_live(self, produit_page):
        produit_page.live = False
        produit_page.save(update_fields=["live"])
        search_term = produit_page.produit_page_search_term

        indexed = ProduitPageSearchTerm.get_indexed_objects()
        assert search_term not in indexed


@pytest.mark.django_db
class TestSearchableQuerySet:
    """SearchTerm.objects.searchable() excludes the same items
    as get_indexed_objects."""

    def test_excludes_synonyme_with_imported_as_search_tag(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        tag = SearchTag.objects.create(name="lave-linge", slug="lave-linge")
        synonyme.imported_as_search_tag = tag
        synonyme.save(update_fields=["imported_as_search_tag"])

        searchable_ids = list(
            SearchTerm.objects.searchable().values_list("id", flat=True)
        )
        assert synonyme.searchterm_ptr_id not in searchable_ids

    def test_includes_synonyme_without_imported_as_search_tag(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)

        searchable_ids = list(
            SearchTerm.objects.searchable().values_list("id", flat=True)
        )
        assert synonyme.searchterm_ptr_id in searchable_ids

    def test_excludes_search_tag_without_page(self):
        tag = SearchTag.objects.create(name="frigo", slug="frigo")

        searchable_ids = list(
            SearchTerm.objects.searchable().values_list("id", flat=True)
        )
        assert tag.searchterm_ptr_id not in searchable_ids

    def test_includes_search_tag_with_page(self, produit_page):
        tag = SearchTag.objects.create(name="frigo", slug="frigo")
        TaggedSearchTag.objects.create(tag=tag, content_object=produit_page)

        searchable_ids = list(
            SearchTerm.objects.searchable().values_list("id", flat=True)
        )
        assert tag.searchterm_ptr_id in searchable_ids

    def test_excludes_produit_page_search_term_on_non_live_page(self, produit_page):
        produit_page.live = False
        produit_page.save(update_fields=["live"])
        search_term = produit_page.produit_page_search_term

        searchable_ids = list(
            SearchTerm.objects.searchable().values_list("id", flat=True)
        )
        assert search_term.searchterm_ptr_id not in searchable_ids

    def test_includes_produit_page_search_term_on_live_page(self, produit_page):
        search_term = produit_page.produit_page_search_term

        searchable_ids = list(
            SearchTerm.objects.searchable().values_list("id", flat=True)
        )
        assert search_term.searchterm_ptr_id in searchable_ids
