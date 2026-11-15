import pytest

from qfdmd.templatetags.qfdmd_tags import as_paragraphs


class TestAsParagraphs:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("Texte seul", "<p>Texte seul</p>"),
            ("Un<br/><br/>Deux", "<p>Un</p><p>Deux</p>"),
            ("Un<br>Deux", "<p>Un<br>Deux</p>"),
            ("<p>Déjà</p>", "<p>Déjà</p>"),
            ("<ul><li>a</li></ul>", "<ul><li>a</li></ul>"),
            ("", ""),
        ],
    )
    def test_wraps_only_text_without_block_element(self, value, expected):
        assert as_paragraphs(value) == expected
