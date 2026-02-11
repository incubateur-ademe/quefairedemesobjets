import pytest
from wagtail.models import Page

from qfdmd.models import (
    Produit,
    ProduitIndexPage,
    ProduitPage,
    SearchTag,
    Synonyme,
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


class TestSynonymeCreatesSearchTerm:
    @pytest.mark.django_db
    def test_creating_synonyme_creates_search_term(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)

        assert SearchTerm.objects.filter(pk=synonyme.searchterm_ptr_id).exists()

    @pytest.mark.django_db
    def test_updating_synonyme_preserves_search_term(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        original_ptr_id = synonyme.searchterm_ptr_id

        synonyme.nom = "Machine à laver"
        synonyme.save()
        synonyme.refresh_from_db()

        assert synonyme.searchterm_ptr_id == original_ptr_id
        assert SearchTerm.objects.filter(pk=original_ptr_id).exists()

    @pytest.mark.django_db
    def test_deleting_synonyme_removes_search_term(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        ptr_id = synonyme.searchterm_ptr_id

        synonyme.delete()

        assert not SearchTerm.objects.filter(pk=ptr_id).exists()


class TestSearchTagCreatesSearchTerm:
    @pytest.mark.django_db
    def test_creating_search_tag_creates_search_term(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")

        assert SearchTerm.objects.filter(pk=tag.searchterm_ptr_id).exists()

    @pytest.mark.django_db
    def test_updating_search_tag_preserves_search_term(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        original_ptr_id = tag.searchterm_ptr_id

        tag.name = "frigo"
        tag.slug = "frigo"
        tag.save()
        tag.refresh_from_db()

        assert tag.searchterm_ptr_id == original_ptr_id
        assert SearchTerm.objects.filter(pk=original_ptr_id).exists()

    @pytest.mark.django_db
    def test_deleting_search_tag_removes_search_term(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        ptr_id = tag.searchterm_ptr_id

        tag.delete()

        assert not SearchTerm.objects.filter(pk=ptr_id).exists()


class TestSearchTermSpecificResolution:
    @pytest.mark.django_db
    def test_specific_returns_synonyme(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        search_term = SearchTerm.objects.get(pk=synonyme.searchterm_ptr_id)

        specific = search_term.specific
        assert isinstance(specific, Synonyme)
        assert specific.pk == synonyme.pk

    @pytest.mark.django_db
    def test_specific_returns_search_tag(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        search_term = SearchTerm.objects.get(pk=tag.searchterm_ptr_id)

        specific = search_term.specific
        assert isinstance(specific, SearchTag)
        assert specific.pk == tag.pk

    @pytest.mark.django_db
    def test_search_result_template_for_synonyme(self, produit):
        synonyme = Synonyme.objects.create(nom="Lave-linge", produit=produit)
        search_term = SearchTerm.objects.get(pk=synonyme.searchterm_ptr_id)

        assert (
            search_term.specific.search_result_template
            == "ui/components/search/search_result_synonyme.html"
        )

    @pytest.mark.django_db
    def test_search_result_template_for_search_tag(self):
        tag = SearchTag.objects.create(name="réfrigérateur", slug="refrigerateur")
        search_term = SearchTerm.objects.get(pk=tag.searchterm_ptr_id)

        assert (
            search_term.specific.search_result_template
            == "ui/components/search/search_result_searchtag.html"
        )

    @pytest.mark.django_db
    def test_search_result_template_for_produit_page(self, produit_page):
        assert (
            produit_page.search_result_template
            == "ui/components/search/search_result_produitpage.html"
        )
