import pytest
from crawl.tasks.business_logic.solve.syntax import url_solve_syntax


class TestUrlSyntaxSuggestReplacements:

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            # Cas valides
            # On Priorise les URLs HTTPS
            ("http://a.com", ["https://a.com", "http://a.com"]),
            # Cas de nettoyage
            ("ahttps://b.com", ["https://b.com"]),
            ("c.com", ["https://c.com"]),
            # Vide
            (None, None),
            ("", None),
            ("   ", None),
        ],
    )
    def test_crawl_urls_solve_syntax(self, url, expected):
        assert url_solve_syntax(url) == expected
