import pandas as pd
import pytest
from core.models.constants import EMPTY_ACTEUR_FIELD

from dags.crawl.config.cohorts import COHORTS
from dags.crawl.config.columns import COLS
from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory

ID = "identifiant_unique"
UNREACHABLE = "azoei1111iqlsk33333nazoienazoiuqoicsu"


@pytest.fixture
def df_read() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "debug_id": ["empty1", "empty2", "success1", "fail1", "fail2"],
            COLS.URL_ORIGIN: [
                None,
                "",
                "http://example.org",
                f"https://{UNREACHABLE}.net",
                f"http://{UNREACHABLE}.com",
            ],
            COLS.URLS_TO_TRY: [
                None,  # should be ignored
                ["", ""],  # should be ignored
                ["https://example.org", "http://example.org"],
                [f"https://{UNREACHABLE}.net"],
                [f"https://{UNREACHABLE}.com", f"http://{UNREACHABLE}.com"],
            ],
        }
    )


@pytest.fixture
def df_syntax_fail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COLS.URL_ORIGIN: ["pas d'URL", "NA"],
            COLS.CRAWL_URL_SUCCESS: [EMPTY_ACTEUR_FIELD] * 2,
            COLS.ACTEURS: [[{ID: "syn1"}], [{ID: "syn2"}, {ID: "syn3"}]],
            COLS.URLS_RESULTS: [None] * 2,
            COLS.COHORT: [COHORTS.SYNTAX_FAIL] * 2,
            COLS.SUGGEST_VALUE: [EMPTY_ACTEUR_FIELD] * 2,
        }
    )


@pytest.fixture
def df_dns_fail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COLS.URL_ORIGIN: ["https://not.found1", "https://not.found2"],
            COLS.CRAWL_URL_SUCCESS: [EMPTY_ACTEUR_FIELD] * 2,
            COLS.ACTEURS: [[{ID: "dns1"}], [{ID: "dns2"}, {ID: "dns3"}]],
            COLS.URLS_RESULTS: [None] * 2,
        }
    )


@pytest.fixture
def df_dns_ok() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COLS.URL_ORIGIN: ["http://localhost/200", "http://localhost/400"],
            COLS.URLS_TO_TRY: [["http://localhost/200"], ["http://localhost/400"]],
            COLS.DOMAINS_TO_TRY: [["localhost"], ["localhost"]],
            COLS.ACTEURS: [[{ID: "dns1"}], [{ID: "dns2"}, {ID: "dns3"}]],
        }
    )


@pytest.fixture
def df_crawl_ok_same() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COLS.URL_ORIGIN: ["https://example.org"],
            COLS.CRAWL_URL_SUCCESS: ["https://example.org"],
            COLS.ACTEURS: [[{ID: "same1"}, {ID: "same2"}, {ID: "same3"}]],
            COLS.URLS_RESULTS: [
                [{COLS.CRAWL_URL_SUCCESS: True, "status_code": 200, "error": None}]
            ],
        }
    )


@pytest.fixture
def df_crawl_ok_diff() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COLS.URL_ORIGIN: ["http://a.com", "http://b.com"],
            COLS.CRAWL_URL_SUCCESS: ["https://a.com", "https://b.com"],
            COLS.ACTEURS: [[{ID: "diff1"}], [{ID: "diff2"}, {ID: "diff3"}]],
            COLS.URLS_RESULTS: [
                [{COLS.CRAWL_URL_SUCCESS: True, "status_code": 200, "error": None}]
            ]
            * 2,
        }
    )


@pytest.fixture
def df_crawl_fail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COLS.URL_ORIGIN: ["url5", "url6", "url7"],
            COLS.CRAWL_URL_SUCCESS: [EMPTY_ACTEUR_FIELD] * 3,
            COLS.ACTEURS: [
                [{ID: "a8"}],
                [{ID: "a9"}],
                [{ID: "a10"}, {ID: "a11"}, {ID: "a12"}],
            ],
            COLS.URLS_RESULTS: [
                [{COLS.CRAWL_URL_SUCCESS: False, "status_code": 404, "error": "error"}]
            ]
            * 3,
        }
    )


@pytest.fixture
def df_all_suggestions(
    df_syntax_fail, df_dns_fail, df_crawl_ok_diff, df_crawl_fail
) -> pd.DataFrame:
    return pd.concat(
        [df_syntax_fail, df_dns_fail, df_crawl_ok_diff, df_crawl_fail],
        ignore_index=True,
    )


def acteurs_create(dfs: list[pd.DataFrame]) -> None:
    df = pd.concat(dfs, ignore_index=True)
    for _, row in df.iterrows():
        for acteur in row[COLS.ACTEURS]:
            RevisionActeurFactory(identifiant_unique=acteur[ID])
