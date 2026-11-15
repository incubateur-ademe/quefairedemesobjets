import pytest
from wagtail.models import Site

from core.views import SITEMAP_MAX_DEPTH, _sitemap_entries
from unit_tests.qfdmd.qfdmod_factory import PageFactory, ProduitPageFactory


def _depth(entries):
    return 0 if not entries else 1 + max(_depth(entry["children"]) for entry in entries)


@pytest.mark.django_db
class TestSitemapEntries:
    @pytest.fixture
    def root(self):
        return Site.objects.get(is_default_site=True).root_page

    def test_tree_is_cut_at_max_depth(self, root):
        level_1 = PageFactory(parent=root)
        level_2 = PageFactory(parent=level_1)
        level_3 = PageFactory(parent=level_2)
        PageFactory(parent=level_3)

        entries = _sitemap_entries(root, SITEMAP_MAX_DEPTH, False)

        assert _depth(entries) == 2
        assert entries[0]["page"].pk == level_1.pk
        assert entries[0]["children"][0]["page"].pk == level_2.pk
        assert entries[0]["children"][0]["children"] == []

    def test_produit_pages_are_excluded(self, root):
        kept = PageFactory(parent=root)
        ProduitPageFactory(parent=root)

        entries = _sitemap_entries(root, SITEMAP_MAX_DEPTH, False)

        assert [entry["page"].pk for entry in entries] == [kept.pk]
