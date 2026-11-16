import pytest
from django.template import Context, Template
from django.test import RequestFactory

from qfdmd.footnotes import make_footnotes_accessible
from qfdmd.models import AccessibilitySettings

LABELS = {
    "call_label": "Note de bas de page",
    "back_label": "retour au texte",
    "list_label": "Notes de bas de page",
}

HTML = (
    '<p>Texte (<a href="#sources">1</a>) et (<a href="#sources">1</a>).</p>'
    '<div id="sources"></div>'
    '<p><b>Sources :</b></p><p>(1) <a href="https://example.org">Source</a></p>'
)


class TestMakeFootnotesAccessible:
    def test_rewrites_calls_and_notes(self):
        result = make_footnotes_accessible(HTML, **LABELS)

        assert 'id="appel-note-1"' in result
        assert 'id="appel-note-1-2"' in result
        assert 'aria-describedby="note-1"' in result
        assert '<li id="note-1" tabindex="-1">' in result
        assert 'aria-label="[1] retour au texte">[1]</a>' in result

    def test_leaves_unmatched_numbers_untouched(self):
        html = '<p><a href="#sources">2</a></p><p>(1) Note</p>'

        assert make_footnotes_accessible(html, **LABELS) == html

    def test_leaves_plain_html_untouched(self):
        html = '<p>Rien <a href="#haut">ici</a></p>'

        assert make_footnotes_accessible(html, **LABELS) == html


@pytest.mark.django_db
def test_footnotes_tag_reads_labels_from_settings():
    AccessibilitySettings.objects.create(
        footnote_label="Renvoi",
        footnote_back_label="revenir",
        footnotes_list_label="Renvois",
    )
    template = Template(
        "{% load qfdmd_tags %}{% footnotes %}" + HTML + "{% endfootnotes %}"
    )

    result = template.render(Context({"request": RequestFactory().get("/")}))

    assert 'aria-label="Renvoi 1"' in result
    assert 'aria-label="[1] revenir"' in result
    assert 'aria-label="Renvois"' in result
