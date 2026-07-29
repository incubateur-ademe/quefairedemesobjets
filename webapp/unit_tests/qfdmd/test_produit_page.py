import pytest

from qfdmd.models import _ensure_wrapped_in_paragraph, _repair_html, _split_off_embeds
from unit_tests.qfdmd.qfdmod_factory import (
    ProduitFactory,
    ProduitPageFactory,
    SynonymeFactory,
)
from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


@pytest.mark.django_db
class TestProduitPagePartitionedBody:
    """ProduitPage.body is split around the first ``carte_sur_mesure`` or
    ``break`` block so that the iframe only shows what comes before the split.
    """

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

    def test_splits_at_break_block(self):
        page = ProduitPageFactory(
            body=[
                ("paragraph", "<p>avant</p>"),
                ("break", None),
                ("paragraph", "<p>apres</p>"),
            ]
        )

        always_visible = page.body_always_visible
        hidden_in_iframe = page.body_to_hide_in_iframe

        # The break block is a pure marker and is NOT rendered in either partition.
        assert [block.block_type for block in always_visible] == [
            "paragraph",
        ]
        assert [block.block_type for block in hidden_in_iframe] == [
            "paragraph",
        ]
        assert str(hidden_in_iframe[0].value) == "<p>apres</p>"

    def test_carte_block_wins_over_break_when_first(self):
        """When both a carte and a break are present, the first one in stream
        order determines the split point. Here the carte comes first."""
        carte = CarteConfigFactory()
        page = ProduitPageFactory(
            body=[
                ("paragraph", "<p>avant</p>"),
                ("carte_sur_mesure", carte),
                ("break", None),
                ("paragraph", "<p>inter</p>"),
            ]
        )

        always_visible = page.body_always_visible
        hidden_in_iframe = page.body_to_hide_in_iframe

        assert [block.block_type for block in always_visible] == [
            "paragraph",
            "carte_sur_mesure",
        ]
        # The break block is also hidden because it's after the carte split
        assert [block.block_type for block in hidden_in_iframe] == [
            "break",
            "paragraph",
        ]

    def test_break_block_wins_over_carte_when_first(self):
        """When the break comes before the carte, the break is the split
        point and the carte is hidden in the iframe."""
        carte = CarteConfigFactory()
        page = ProduitPageFactory(
            body=[
                ("paragraph", "<p>avant</p>"),
                ("break", None),
                ("paragraph", "<p>inter</p>"),
                ("carte_sur_mesure", carte),
            ]
        )

        always_visible = page.body_always_visible
        hidden_in_iframe = page.body_to_hide_in_iframe

        # The break is excluded (marker), everything before it stays visible
        assert [block.block_type for block in always_visible] == [
            "paragraph",
        ]
        # After the break, even the carte is hidden in the iframe
        assert [block.block_type for block in hidden_in_iframe] == [
            "paragraph",
            "carte_sur_mesure",
        ]

    def test_body_without_split_block_does_not_raise(self):
        # Regression: first_block_by_name returns None when neither a carte
        # nor a break block is present.
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
    """ProduitPage exposes a "Voir plus de recommandations" footer button pointing
    at its own standalone URL, used in the iframe footer."""

    def test_get_context_includes_footer_primary_button(self, rf):
        page = ProduitPageFactory()
        request = rf.get("/")

        ctx = page.get_context(request)

        button = ctx["footer_primary_button"]
        assert button["label"] == "Voir plus de recommandations"
        assert "fr-icon-external-link-line" in button["extra_classes"]
        # The standalone link is tagged so visits from the iframe footer are
        # attributable.
        assert "utm_source=qfdmod" in button["onclick"]


class TestSplitOffEmbeds:
    """_split_off_embeds pulls <script>/<iframe> tags (e.g. the impactco2.fr
    widget) out of legacy rich-text HTML so they can be migrated into their
    own StreamField "html" block instead of a RichTextBlock, which would
    otherwise strip them."""

    def test_no_embed_returns_html_unchanged(self):
        html = "<p>Rien à signaler ici.</p>"

        cleaned, embeds = _split_off_embeds(html)

        assert cleaned == html
        assert embeds == []

    def test_extracts_script_tag(self):
        script = (
            '<script name="impact-co2" src="https://impactco2.fr/iframe.js" '
            'data-type="transport"></script>'
        )
        html = f"<p>avant</p>{script}<p>après</p>"

        cleaned, embeds = _split_off_embeds(html)

        assert embeds == [script]
        assert script not in cleaned
        assert cleaned == "<p>avant</p><p>après</p>"

    def test_extracts_iframe_tag(self):
        iframe = '<iframe src="https://example.com/widget"></iframe>'
        html = f"<p>avant</p>{iframe}"

        cleaned, embeds = _split_off_embeds(html)

        assert embeds == [iframe]
        assert cleaned == "<p>avant</p>"

    def test_extracts_multiple_embeds_in_order(self):
        script = '<script src="https://a.example/x.js"></script>'
        iframe = '<iframe src="https://b.example/y"></iframe>'
        html = f"{script}<p>milieu</p>{iframe}"

        cleaned, embeds = _split_off_embeds(html)

        assert embeds == [script, iframe]
        assert cleaned == "<p>milieu</p>"


@pytest.mark.django_db
class TestSyncFromLegacyProduitEmbeds:
    """sync_from_legacy_produit must not leave raw <script>/<iframe> tags
    inside a RichTextBlock: they get split into a dedicated "html" block."""

    def test_script_in_comment_les_eviter_becomes_its_own_html_block(self):
        script = (
            '<script name="impact-co2" src="https://impactco2.fr/iframe.js" '
            'data-type="transport"></script>'
        )
        produit = ProduitFactory(
            comment_les_eviter=f"Consignes de base.{script}",
        )
        page = ProduitPageFactory()
        produit.legacy_imported_as_produit_page = page
        produit.save(update_fields=["legacy_imported_as_produit_page"])

        page.sync_from_legacy_produit()

        html_blocks = [b for b in page.body if b.block_type == "html"]
        assert len(html_blocks) == 1
        assert str(html_blocks[0].value) == script

        paragraph_blocks = [b for b in page.body if b.block_type == "paragraph"]
        assert not any(script in b.value.source for b in paragraph_blocks)


class TestRepairHtml:
    """_repair_html balances tags in legacy HTML before it is stored as a
    RichTextBlock value. Unbalanced markup (e.g. a stray closing tag with no
    matching opening tag) otherwise crashes Wagtail's contentstate converter
    with "AssertionError: Unmatched tags" as soon as the page is opened in
    the editor."""

    def test_well_formed_html_is_unchanged_in_content(self):
        html = "<p>Rien à signaler</p><b>gras</b>."

        repaired = _repair_html(html)

        assert "Rien à signaler" in repaired
        assert "<b>gras</b>" in repaired

    def test_drops_unmatched_closing_tag(self):
        html = "avant.<br><br></b>après</b>, fin."

        repaired = _repair_html(html)

        assert "</b>après</b>" not in repaired
        assert "après" in repaired
        assert "avant." in repaired
        assert "fin." in repaired


@pytest.mark.django_db
class TestSyncFromLegacyProduitMalformedHtml:
    """sync_from_legacy_produit must not write unbalanced HTML (e.g. a
    stray closing tag with no matching opener) into a RichTextBlock: it
    crashes the page editor with an AssertionError from Wagtail's
    contentstate converter as soon as the malformed value is loaded."""

    def test_unmatched_tag_in_synonyme_bon_etat_is_repaired(self):
        malformed = (
            "Proposez-le à un proche.<br><br></b>S'il est propre</b>, "
            "donnez-le en point de collecte."
        )
        produit = ProduitFactory(nom="Articles en cuir")
        SynonymeFactory(
            nom=produit.nom,
            produit=produit,
            qu_est_ce_que_j_en_fais_bon_etat=malformed,
            qu_est_ce_que_j_en_fais_mauvais_etat="Jetez-le à la poubelle.",
        )
        page = ProduitPageFactory()
        produit.legacy_imported_as_produit_page = page
        produit.save(update_fields=["legacy_imported_as_produit_page"])

        page.sync_from_legacy_produit()

        grid = next(b for b in page.body if b.block_type == "item_grid").value
        description = str(grid["items"][0].value["description"])
        assert "</b>S'il est propre</b>" not in description
        assert "S'il est propre" in description

        # The DraftailRichTextArea widget's format_value() is exactly what
        # crashed on the unbalanced source HTML when the editor loaded it.
        from wagtail.admin.rich_text.editors.draftail import DraftailRichTextArea

        DraftailRichTextArea().format_value(description)


class TestEnsureWrappedInParagraph:
    """_ensure_wrapped_in_paragraph guarantees a card's "description" value
    has a top-level <p> for the DSFR card template's richtext_p_add_class
    filter (which only adds its layout class to existing <p> tags via
    ``soup.find_all("p")``) to attach its CSS class to. Legacy fields are
    plain text with <br> line breaks, not RichText, so they have no <p> of
    their own: with none to target, the description rendered as unwrapped
    text on the live page, breaking the CSS layout that positions the
    title/description/badge (the admin's preview iframe didn't show this,
    since Draftail's contentstate round-trip always wraps top-level text
    in <p>, unlike live rendering which outputs the stored HTML as-is)."""

    def test_wraps_bare_text_in_paragraph(self):
        html = "Proposez-le à un proche.<br><br>Vous pouvez aussi le revendre."

        wrapped = _ensure_wrapped_in_paragraph(html)

        assert wrapped == f"<p>{html}</p>".replace("<br>", "<br/>")

    def test_leaves_already_wrapped_paragraph_untouched(self):
        html = "<p>Déjà encapsulé.</p>"

        wrapped = _ensure_wrapped_in_paragraph(html)

        assert wrapped == html

    def test_leaves_heading_plus_text_untouched(self):
        """A leading block element (e.g. <h2>) is left as-is: wrapping the
        whole thing in one <p> would nest a block element inside it."""
        html = "<h2>Titre</h2>Texte après le titre."

        wrapped = _ensure_wrapped_in_paragraph(html)

        assert wrapped == html


@pytest.mark.django_db
class TestSyncFromLegacyProduitDescriptionWrapping:
    """sync_from_legacy_produit must wrap bare bon_etat/mauvais_etat text in
    a <p> so the DSFR card layout (title/description/badge) renders in the
    right order on the live page, not just in the admin preview."""

    def test_card_descriptions_are_wrapped_in_paragraph(self):
        produit = ProduitFactory(nom="Articles en cuir")
        SynonymeFactory(
            nom=produit.nom,
            produit=produit,
            qu_est_ce_que_j_en_fais_bon_etat=(
                "Proposez-le à un proche.<br><br>Ou revendez-le."
            ),
            qu_est_ce_que_j_en_fais_mauvais_etat="Jetez-le à la poubelle.",
        )
        page = ProduitPageFactory()
        produit.legacy_imported_as_produit_page = page
        produit.save(update_fields=["legacy_imported_as_produit_page"])

        page.sync_from_legacy_produit()

        grid = next(b for b in page.body if b.block_type == "item_grid").value
        bon_etat_desc = str(grid["items"][0].value["description"])
        mauvais_etat_desc = str(grid["items"][1].value["description"])
        assert bon_etat_desc.startswith("<p>")
        assert bon_etat_desc.endswith("</p>")
        assert mauvais_etat_desc.startswith("<p>")
        assert mauvais_etat_desc.endswith("</p>")
