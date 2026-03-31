import pytest
from unittest.mock import call, patch
from wagtail.models import Page, Site
from wagtail.signals import page_published

from qfdmd.models import ProduitIndexPage, ProduitPage, SearchTag, TaggedSearchTag


@pytest.fixture
def root_page():
    root = Page.objects.get(depth=1)
    Site.objects.get_or_create(
        hostname="localhost",
        defaults={
            "root_page": root,
            "is_default_site": True,
            "site_name": "Test Site",
        },
    )
    return root


@pytest.fixture
def produit_index_page(root_page):
    page = ProduitIndexPage(title="Produits", slug="produits")
    root_page.add_child(instance=page)
    return page


@pytest.fixture
def produit_page(produit_index_page):
    page = ProduitPage(title="Lave-linge", slug="lave-linge")
    produit_index_page.add_child(instance=page)
    return page


@pytest.mark.django_db
class TestIndexSearchTagsOnPublish:
    def test_linked_search_tags_are_reindexed(self, produit_page):
        tag1 = SearchTag.objects.create(name="machine à laver", slug="machine-a-laver")
        tag2 = SearchTag.objects.create(name="lavelinge", slug="lavelinge")
        TaggedSearchTag.objects.create(tag=tag1, content_object=produit_page)
        TaggedSearchTag.objects.create(tag=tag2, content_object=produit_page)

        with patch("qfdmd.signals.insert_or_update_object") as mock_insert:
            page_published.send(sender=ProduitPage, instance=produit_page)

        assert mock_insert.call_count == 2
        mock_insert.assert_has_calls(
            [call(tag1), call(tag2)],
            any_order=True,
        )

    def test_no_tags_no_indexing_called(self, produit_page):
        with patch("qfdmd.signals.insert_or_update_object") as mock_insert:
            page_published.send(sender=ProduitPage, instance=produit_page)

        mock_insert.assert_not_called()

    def test_only_tags_linked_to_page_are_reindexed(
        self, produit_page, produit_index_page
    ):
        other_page = ProduitPage(title="Aspirateur", slug="aspirateur")
        produit_index_page.add_child(instance=other_page)

        tag_mine = SearchTag.objects.create(name="lave-linge", slug="lave-linge")
        tag_other = SearchTag.objects.create(name="aspirateur", slug="aspirateur")
        TaggedSearchTag.objects.create(tag=tag_mine, content_object=produit_page)
        TaggedSearchTag.objects.create(tag=tag_other, content_object=other_page)

        with patch("qfdmd.signals.insert_or_update_object") as mock_insert:
            page_published.send(sender=ProduitPage, instance=produit_page)

        mock_insert.assert_called_once_with(tag_mine)
