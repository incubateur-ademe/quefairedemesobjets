import pytest

from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


@pytest.mark.django_db
class TestProduitPagePartitionedBody:
    """ProduitPage.body is split around the ``carte_sur_mesure`` block so that
    the iframe only shows what comes up to and including the carte."""

    def test_splits_at_carte_block(self):
        carte = CarteConfigFactory()
        page = ProduitPageFactory(
            body=[
                ("paragraph", "<p>avant</p>"),
                ("carte_sur_mesure", carte),
                ("paragraph", "<p>apres</p>"),
            ]
        )

        always_visible = page.body_always_visible
        hidden_in_iframe = page.body_to_hide_in_iframe

        # Everything up to and including the carte stays visible.
        assert [block.block_type for block in always_visible] == [
            "paragraph",
            "carte_sur_mesure",
        ]
        # Only the blocks strictly after the carte are hidden in the iframe.
        assert [block.block_type for block in hidden_in_iframe] == ["paragraph"]
        assert str(hidden_in_iframe[0].value) == "<p>apres</p>"

    def test_carte_is_not_duplicated_across_partitions(self):
        carte = CarteConfigFactory()
        page = ProduitPageFactory(
            body=[
                ("carte_sur_mesure", carte),
                ("paragraph", "<p>apres</p>"),
            ]
        )

        all_ids = [block.id for block in page.body]
        partition_ids = [
            block.id
            for block in [*page.body_always_visible, *page.body_to_hide_in_iframe]
        ]

        # The two partitions together reconstruct the body exactly, no block lost
        # or duplicated.
        assert partition_ids == all_ids
        assert len(set(partition_ids)) == len(all_ids)

    def test_body_without_carte_block_does_not_raise(self):
        # Regression: first_block_by_name returns None when the carte block is
        # absent. Accessing .id on None used to raise AttributeError on every
        # render of such a page.
        page = ProduitPageFactory(
            body=[
                ("paragraph", "<p>un</p>"),
                ("paragraph", "<p>deux</p>"),
            ]
        )

        always_visible = page.body_always_visible
        hidden_in_iframe = page.body_to_hide_in_iframe

        assert [block.block_type for block in always_visible] == [
            "paragraph",
            "paragraph",
        ]
        assert list(hidden_in_iframe) == []

    def test_empty_body(self):
        page = ProduitPageFactory(body=[])

        assert list(page.body_always_visible) == []
        assert list(page.body_to_hide_in_iframe) == []


@pytest.mark.django_db
class TestProduitPageFooterButton:
    """ProduitPage exposes a "Lire plus sur cette fiche" footer button pointing
    at its own standalone URL, used in the iframe footer."""

    def test_get_context_includes_footer_primary_button(self, rf):
        page = ProduitPageFactory()
        request = rf.get("/")

        ctx = page.get_context(request)

        button = ctx["footer_primary_button"]
        assert button["label"] == "Lire plus sur cette fiche"
        assert "fr-icon-external-link-line" in button["extra_classes"]
        # The standalone link is tagged so visits from the iframe footer are
        # attributable.
        assert "utm_source=qfdmod" in button["onclick"]
        assert "_blank" in button["onclick"]
