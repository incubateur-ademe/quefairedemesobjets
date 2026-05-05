"""Tests for the RGAA Mineurs Lookbook previews.

Each preview demonstrates one of the fixes shipped under the
`accessibilite-rgaa-mineurs` branch. We just check the templates render
without errors and contain the expected ARIA / link markers.
"""

from django.template.loader import render_to_string


def test_skip_link_demo_renders_dsfr_skiplinks():
    html = render_to_string(
        "ui/components/accessibilite/skip_link_demo.html",
        {"skiplinks": [{"link": "#content", "label": "Contenu"}]},
    )
    assert 'class="fr-skiplinks"' in html
    assert 'href="#content"' in html
    assert 'id="content"' in html


def test_landmarks_demo_lists_all_landmarks():
    html = render_to_string("ui/components/accessibilite/landmarks_demo.html")
    assert 'role="banner"' in html
    assert 'role="main"' in html
    assert 'role="contentinfo"' in html
    assert 'aria-label="Pour aller plus loin"' in html


def test_iframe_titles_demo_lists_each_route():
    html = render_to_string("ui/components/accessibilite/iframe_titles_demo.html")
    assert "Carte Longue Vie aux Objets" in html
    assert "Formulaire de recherche de solutions de réemploi" in html
    assert "Info-tri" in html
    assert "data-title" in html


def test_svg_decoratifs_demo_includes_aria_hidden_logos():
    html = render_to_string("ui/components/accessibilite/svg_decoratifs_demo.html")
    # Each logo SVG carries aria-hidden="true" focusable="false" thanks to A11Y-11.
    assert html.count('aria-hidden="true"') >= 3
    assert html.count('focusable="false"') >= 3


def test_liens_explicites_demo_demonstrates_both_fixes():
    html = render_to_string("ui/components/accessibilite/liens_explicites_demo.html")
    # 1. The header logo link gets a sr-only span.
    assert 'class="qf-sr-only"' in html
    # 2. The "disponible librement" link's title was rewritten.
    assert 'title="disponible librement - Nouvelle fenêtre"' in html
