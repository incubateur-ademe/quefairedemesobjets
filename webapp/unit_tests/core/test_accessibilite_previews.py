"""Tests des previews du lookbook AccessibilitePreview pour les correctifs RGAA.

Chaque test correspond à une carte du backlog Notion :
- A11Y-3 : fil d'ariane sur les pages produit
- A11Y-9 : tooltip de partage de la fiche acteur sans tabindex="-1"
- A11Y-6 : champs facultatifs marqués au lieu des obligatoires
- A11Y-10 : disclaimer « pas de solution localisée » avec role="status"
"""

import pytest

from previews.template_preview import AccessibilitePreview


@pytest.fixture
def preview():
    return AccessibilitePreview()


class TestFilArianeProduit:
    """A11Y-3 — fil d'ariane sur ProduitPage / FamilyPage."""

    def test_breadcrumb_is_rendered(self, preview):
        html = preview.fil_ariane_dans_heading_produit()
        assert 'class="fr-breadcrumb"' in html

    def test_last_item_has_href_for_keyboard_reach(self, preview):
        """RGAA 7.3 : le dernier élément doit être atteignable au clavier."""
        html = preview.fil_ariane_dans_heading_produit()
        assert 'href="#" aria-current="page"' in html

    def test_intermediate_items_have_real_href(self, preview):
        html = preview.fil_ariane_dans_heading_produit()
        assert 'href="/categories/"' in html


class TestShareTooltipActeur:
    """A11Y-9 — tooltip de partage sans tabindex="-1"."""

    def test_no_tabindex_minus_one_on_links_or_button(self, preview):
        """RGAA 7.3 : les liens et le bouton doivent rester atteignables au clavier."""
        html = preview.share_tooltip_acteur_sans_tabindex()
        assert 'tabindex="-1"' not in html

    def test_all_share_links_present(self, preview):
        html = preview.share_tooltip_acteur_sans_tabindex()
        for css_class in (
            "fr-btn--facebook",
            "fr-btn--twitter-x",
            "fr-btn--linkedin",
            "fr-btn--mail",
            "fr-btn--copy",
        ):
            assert css_class in html


class TestChampsFacultatifsMarques:
    """A11Y-6 — DSFR_MARK_OPTIONAL_FIELDS=True."""

    def test_no_required_asterisk_marker(self, preview):
        """RGAA 11.10 : les champs obligatoires ne sont plus marqués d'un astérisque."""
        html = preview.champs_facultatifs_marques()
        assert 'class="fr-required-marker"' not in html

    def test_optional_field_is_marked(self, preview):
        """Le label du champ facultatif est annoté « (Optionnel) »."""
        html = preview.champs_facultatifs_marques()
        assert "(Optionnel)" in html


class TestNoLocalSolutionRoleStatus:
    """A11Y-10 — role="status" sur le disclaimer pas de solution."""

    def test_role_status_is_present(self, preview):
        """RGAA 7.5 : le message dynamique est annoncé par les TA via role="status"."""
        html = preview.no_local_solution_role_status()
        assert 'role="status"' in html

    def test_message_is_rendered(self, preview):
        html = preview.no_local_solution_role_status()
        assert "Il n'existe pas de solution" in html
