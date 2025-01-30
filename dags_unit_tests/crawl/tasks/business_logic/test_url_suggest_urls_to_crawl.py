import pytest

from dags.crawl.tasks.business_logic import url_suggest_urls_to_crawl


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
    def test_url_suggest_urls_to_crawl(self, url, expected):
        assert url_suggest_urls_to_crawl(url) == expected
