import pytest
from crawl.fixtures import UNREACHABLE, df_read  # noqa: F401

from core.models.constants import EMPTY_ACTEUR_FIELD
from dags.crawl.config.cohorts import COHORTS
from dags.crawl.config.columns import COLS
from dags.crawl.tasks.business_logic.crawl_urls_check_dns import (
    crawl_urls_check_dns,
    dns_is_ok,
)


class TestDomainIsReachable:

    @pytest.mark.parametrize(
        ("domain", "expected"),
        [
            # Valid syntax & DNS resolution
            ("example.org", True),
            # Valid syntax but no DNS resolution
            (f"{UNREACHABLE}.fr", False),
            # Invalid syntax
            ("google", False),
            # Empty cases
            ("  ", False),
            (None, False),
        ],
    )
    def test_domain_is_reachable(self, domain, expected):
        assert dns_is_ok(domain) == expected


class TestCrawUrlsCheckDns:

    @pytest.fixture
    def df_results(self, df_read):  # noqa: F811
        return crawl_urls_check_dns(df_read)

    @pytest.fixture
    def df_domains_ok(self, df_results):
        return df_results[0]

    @pytest.fixture
    def df_domains_fail(self, df_results):
        return df_results[1]

    def test_columns(self, df_domains_ok, df_domains_fail):
        assert COLS.DOMAINS_TO_TRY in df_domains_ok.columns
        assert COLS.DOMAINS_RESULTS in df_domains_ok.columns
        assert COLS.DNS_OK in df_domains_ok.columns
        assert COLS.DOMAINS_TO_TRY in df_domains_fail.columns
        assert COLS.DOMAINS_RESULTS in df_domains_fail.columns
        assert COLS.DNS_OK in df_domains_fail.columns

    def test_no_duplicate_domains(self, df_domains_ok):
        # Even if there are multiple candidate URLs, we don't
        # try to reach the same domain multiple times
        assert df_domains_ok[COLS.DOMAINS_TO_TRY].tolist() == [
            ["example.org"],
        ]

    def test_domains_ok(self, df_domains_ok):
        assert df_domains_ok["debug_id"].tolist() == ["success1"]

    def test_domains_fail(self, df_domains_fail):
        assert sorted(df_domains_fail["debug_id"].tolist()) == sorted(
            [
                "fail1",
                "fail2",
            ]
        )

    def test_empty_domains_not_evaluated(self, df_domains_ok, df_domains_fail):
        # We shouldn't consider invalid URLs (thus no domains) neither
        # as part of DNS success or failure, they are just things we ignore
        # as they are not a DNS issue per se
        assert "empty1" not in df_domains_ok["debug_id"].tolist()
        assert "empty2" not in df_domains_ok["debug_id"].tolist()
        assert "empty1" not in df_domains_fail["debug_id"].tolist()
        assert "empty2" not in df_domains_fail["debug_id"].tolist()

    def test_suggestion_cohort_and_values(self, df_domains_ok, df_domains_fail):
        # We have no suggestion to make if DNS is OK
        assert COLS.SUGGEST_VALUE not in df_domains_ok.columns
        # We have cohort for the same of consistency
        assert all(df_domains_ok[COLS.COHORT] == COHORTS.DNS_OK)

        # And for the failed case, suggestion is to set empty
        assert all(df_domains_fail[COLS.SUGGEST_VALUE] == EMPTY_ACTEUR_FIELD)
        assert all(df_domains_fail[COLS.COHORT] == COHORTS.DNS_FAIL)
