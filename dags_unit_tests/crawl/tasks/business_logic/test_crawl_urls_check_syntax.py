import pytest
from crawl.fixtures import df_read  # noqa: F401
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD

from dags.crawl.config.cohorts import COHORTS
from dags.crawl.config.columns import COLS
from dags.crawl.tasks.business_logic.crawl_urls_check_syntax import (
    crawl_urls_check_syntax,
    url_domain_get,
    url_is_valid,
    url_protocol_fix,
    url_to_urls_to_try,
    urls_are_http_https_versions,
)


class TestUrlIsValid:

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            # Valid cases
            ("http://a.com", True),
            ("https://b.com", True),
            # Although technically valid, we don't want to support
            # ports in our URLs, so we flag these
            ("https://www.c.com:8080", False),
            # Empty cases
            (None, False),
            ("", False),
            ("   ", False),
            # Invalid cases
            ("a.com", False),
            ("https://", False),
            ("https://.", False),
            ("https://.com", False),
        ],
    )
    def test_crawl_url_is_valid(self, url, expected):
        assert url_is_valid(url) == expected


class TestUrlsAreHttpAndHttpsVersions:

    @pytest.mark.parametrize(
        ("url1", "url2", "expected"),
        [
            # Valid cases
            ("http://a.com", "https://a.com", True),
            ("https://b.com", "http://b.com", True),
            ("https://c.com", "https://c.com", True),
            # Empty cases
            ("  ", "", False),
            ("", "https://a.com", False),
            ("http://a.com", "", False),
            # Different domains
            ("http://a.com", "http://b.com", False),
            ("https://a.com", "https://b.com", False),
        ],
    )
    def test_crawl_urls_are_http_and_https_versions(self, url1, url2, expected):
        assert urls_are_http_https_versions(url1, url2) == expected


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
            # We don't tolerate ports in URLs, thus we
            # don't try to extract the domain
            ("https://www.c.com:8080", None),
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


class TestCrawlUrlsCheckSyntax:

    @pytest.fixture
    def df_results(self, df_read):  # noqa: F811
        return crawl_urls_check_syntax(df=df_read)

    @pytest.fixture
    def df_syntax_ok(self, df_results):
        return df_results[0]

    @pytest.fixture
    def df_syntax_fail(self, df_results):
        return df_results[1]

    def test_df_syntax_ok(self, df_syntax_ok):
        assert all(df_syntax_ok[COLS.COHORT] == COHORTS.SYNTAX_OK)
        assert COLS.SUGGEST_VALUE not in df_syntax_ok.columns

    def test_df_syntax_fail(self, df_syntax_fail):
        assert all(df_syntax_fail[COLS.COHORT] == COHORTS.SYNTAX_FAIL)
        assert all(df_syntax_fail[COLS.SUGGEST_VALUE] == EMPTY_ACTEUR_FIELD)
