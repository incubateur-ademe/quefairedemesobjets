import pytest
from django.test import Client
from modelsearch.index import insert_or_update_object
from wagtail.models import Page

from qfdmd.models import (
    Produit,
    ProduitIndexPage,
    ProduitPage,
    SearchTag,
    Synonyme,
    TaggedSearchTag,
)


@pytest.fixture
def produit_page():
    root = Page.objects.get(depth=1)
    index_page = ProduitIndexPage(title="Products", slug="products")
    root.add_child(instance=index_page)
    page = ProduitPage(
        title="Lave-linge",
        slug="lave-linge",
        titre_phrase="Lave-linge",
    )
    index_page.add_child(instance=page)
    return page


@pytest.fixture
def search_tag_on_page(produit_page):
    tag = SearchTag.objects.create(name="lave-linge", slug="lave-linge")
    TaggedSearchTag.objects.create(tag=tag, content_object=produit_page)
    # Re-index after linking to page (the initial post_save skipped indexing
    # because the tag had no page link yet)
    insert_or_update_object(tag)
    return tag


@pytest.fixture
def synonyme():
    produit = Produit.objects.create(nom="Lave-linge")
    return Synonyme.objects.create(nom="Lave-linge", produit=produit)


@pytest.mark.django_db
class TestSearchViewResultTypes:
    """Searching returns Synonyme and SearchTag results through the unified
    SearchTerm search endpoint."""

    def test_synonyme_and_search_tag_returned(
        self, produit_page, search_tag_on_page, synonyme
    ):
        client = Client()
        response = client.get(
            "/assistant/recherche",
            {"home-id": "home", "home-input": "lave-linge"},
        )
        assert response.status_code == 200

        form = response.context["search_form"]
        results = form.results

        specific_types = {type(r.specific).__name__ for r in results}
        assert "Synonyme" in specific_types
        assert "SearchTag" in specific_types


@pytest.mark.django_db
class TestSearchViewSearchTagLinkParams:
    """SearchTag results render with search_term_id, position, and search_term
    query parameters in their href."""

    def test_search_tag_link_contains_all_params(
        self, produit_page, search_tag_on_page
    ):
        client = Client()
        response = client.get(
            "/assistant/recherche",
            {"home-id": "home", "home-input": "lave-linge"},
        )
        assert response.status_code == 200
        content = response.content.decode()

        # The link should contain search_term_id=<tag pk>
        assert f"search_term_id={search_tag_on_page.pk}" in content
        # The link should contain position=
        assert "position=" in content
        # The link should contain search_term=lave-linge
        assert "search_term=lave-linge" in content

    def test_search_tag_result_shows_parent_page_title(
        self, produit_page, search_tag_on_page
    ):
        client = Client()
        response = client.get(
            "/assistant/recherche",
            {"home-id": "home", "home-input": "lave-linge"},
        )
        content = response.content.decode()

        # The result should display the parent page's titre_phrase
        assert "Lave-linge" in content
