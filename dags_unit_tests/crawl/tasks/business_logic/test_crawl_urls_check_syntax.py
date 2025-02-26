import pytest

from dags.crawl.tasks.business_logic.crawl_urls_check_syntax import (
    url_domain_get,
    url_protocol_fix,
    url_to_urls_to_try,
)


class TestUrlProtocolFix:

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            # Valid cases we should preserve
            ("http://a.com", "http://a.com"),
            ("https://b.com", "https://b.com"),
            # Noise before http
            ("ahttps://c.com", "https://c.com"),
            # Missing http
            ("c.com", "https://c.com"),
            # The // case
            ("//d.com", "https://d.com"),
            # : missing
            ("https//b.com", "https://b.com"),
            # : too many
            ("https::://b.com", "https://b.com"),
            # One /
            ("https:/c.com", "https://c.com"),
            # // missing
            ("https:c.com", "https://c.com"),
            # // too many
            ("https:///c.com", "https://c.com"),
            # Full mess
            ("ahttps::///c.com", "https://c.com"),
        ],
    )
    def test_crawl_url_protocol_fix(self, url, expected):
        assert url_protocol_fix(url) == expected


class TestUrlDomainGet:

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            # Valid cases
            ("http://a.com", "a.com"),
            ("https://b.com", "b.com"),
            ("https://www.c.com:8080", "www.c.com"),
            # Empty
            (None, None),
            ("", None),
            ("   ", None),
        ],
    )
    def test_crawl_url_domain_get(self, url, expected):
        assert url_domain_get(url) == expected


class TestUrlSyntaxSuggestReplacements:

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            # Valid cases
            # We always add a https version if missing
            ("http://a.com", ["https://a.com", "http://a.com"]),
            # Cleanup cases
            ("ahttps://b.com", ["https://b.com"]),
            ("https:://b.com", ["https://b.com"]),
            ("https::://b.com", ["https://b.com"]),
            ("https:/c.com", ["https://c.com"]),
            ("https:///c.com", ["https://c.com"]),
            ("c.com", ["https://c.com"]),
            # Spaces in middle
            ("  https:// NOT A WEBWITE  ", None),
            # Typical dirty values we see in DB
            ("NA", None),
            ("nan", None),
            ("none", None),
            # Empty cases returning None as clear
            # signal we can't suggest anything
            (None, None),
            ("", None),
            ("   ", None),
        ],
    )
    def test_url_to_urls_to_try(self, url, expected):
        assert url_to_urls_to_try(url) == expected
