import pandas as pd
import pytest

from dags.crawl.config.constants import (
    COL_DOMAIN_SUCCESS,
    COL_DOMAINS_RESULTS,
    COL_DOMAINS_TO_TRY,
    COL_URLS_TO_TRY,
)
from dags.crawl.tasks.business_logic.crawl_urls_check_dns import (
    crawl_urls_check_dns,
    dns_is_ok,
)

INVALID_DOMAIN = "azoei1111iqlsk33333nazoienazoiuqoicsu.com"


class TestDomainIsReachable:

    @pytest.mark.parametrize(
        ("domain", "expected"),
        [
            ("example.org", True),
            ("azpeoiazpeoiazpncvaozieuaozieulqksqcnaze.fr", False),
            ("", False),
            (None, False),
        ],
    )
    def test_domain_is_reachable(self, domain, expected):
        assert dns_is_ok(domain) == expected


class TestCrawUrlsSolveReachDomains:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                "debug_id": ["fail1", "fail2", "success1", "fail3", "fail4"],
                COL_URLS_TO_TRY: [
                    None,
                    ["", ""],
                    ["https://example.org", "http://example.org"],
                    [],
                    [f"https://{INVALID_DOMAIN}", f"http://{INVALID_DOMAIN}"],
                ],
            }
        )

    @pytest.fixture
    def df_results(self, df):
        return crawl_urls_check_dns(df)

    @pytest.fixture
    def df_domains_ok(self, df_results):
        return df_results[0]

    @pytest.fixture
    def df_domains_fail(self, df_results):
        return df_results[1]

    def test_columns(self, df_domains_ok, df_domains_fail):
        assert COL_DOMAINS_TO_TRY in df_domains_ok.columns
        assert COL_DOMAINS_RESULTS in df_domains_ok.columns
        assert COL_DOMAIN_SUCCESS in df_domains_ok.columns
        assert COL_DOMAINS_TO_TRY in df_domains_fail.columns
        assert COL_DOMAINS_RESULTS in df_domains_fail.columns
        assert COL_DOMAIN_SUCCESS in df_domains_fail.columns

    def test_no_duplicate_domains(self, df_domains_ok):
        # Even if there are multiple candidate URLs, we don't
        # try to reach the same domain multiple times
        assert df_domains_ok[COL_DOMAINS_TO_TRY].tolist() == [
            ["example.org"],
        ]

    def test_domains_ok(self, df_domains_ok):
        assert df_domains_ok["debug_id"].tolist() == ["success1"]

    def test_domains_fail(self, df_domains_fail):
        assert df_domains_fail["debug_id"].tolist() == [
            "fail1",
            "fail2",
            "fail3",
            "fail4",
        ]
