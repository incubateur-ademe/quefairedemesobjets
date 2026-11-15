from qfdmd.footnotes import make_footnotes_accessible

HTML = (
    '<p>Texte (<a href="#sources">1</a>) et (<a href="#sources">1</a>).</p>'
    '<div id="sources"></div>'
    '<p><b>Sources :</b></p><p>(1) <a href="https://example.org">Source</a></p>'
)


class TestMakeFootnotesAccessible:
    def test_rewrites_calls_and_notes(self):
        result = make_footnotes_accessible(HTML)

        assert 'id="appel-note-1"' in result
        assert 'id="appel-note-1-2"' in result
        assert 'aria-describedby="note-1"' in result
        assert '<li id="note-1" tabindex="-1">' in result
        assert 'aria-label="[1] retour au texte">[1]</a>' in result

    def test_leaves_unmatched_numbers_untouched(self):
        html = '<p><a href="#sources">2</a></p><p>(1) Note</p>'

        assert make_footnotes_accessible(html) == html

    def test_leaves_plain_html_untouched(self):
        html = '<p>Rien <a href="#haut">ici</a></p>'

        assert make_footnotes_accessible(html) == html
