import pandas as pd
import pytest
from crawl.config.constants import (
    COL_ACTEURS,
    COL_URL_ORIGINAL,
    COL_URL_SUCCESS,
    COL_URLS_RESULTS,
)
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD

from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory

ID = "identifiant_unique"


@pytest.fixture
def df_syntax_fail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_URL_ORIGINAL: ["pas d'URL", "NA"],
            COL_URL_SUCCESS: [EMPTY_ACTEUR_FIELD] * 2,
            COL_ACTEURS: [[{ID: "syn1"}], [{ID: "syn2"}, {ID: "syn3"}]],
            COL_URLS_RESULTS: [None] * 2,
        }
    )


@pytest.fixture
def df_dns_fail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_URL_ORIGINAL: ["https://not.found1", "https://not.found2"],
            COL_URL_SUCCESS: [EMPTY_ACTEUR_FIELD] * 2,
            COL_ACTEURS: [[{ID: "dns1"}], [{ID: "dns2"}, {ID: "dns3"}]],
            COL_URLS_RESULTS: [None] * 2,
        }
    )


@pytest.fixture
def df_urls_ok_same() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_URL_ORIGINAL: ["https://example.org"],
            COL_URL_SUCCESS: ["https://example.org"],
            COL_ACTEURS: [[{ID: "same1"}, {ID: "same2"}, {ID: "same3"}]],
            COL_URLS_RESULTS: [
                [{"was_success": True, "status_code": 200, "error": None}]
            ],
        }
    )


@pytest.fixture
def df_urls_ok_diff() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_URL_ORIGINAL: ["http://a.com", "http://b.com"],
            COL_URL_SUCCESS: ["https://a.com", "https://b.com"],
            COL_ACTEURS: [[{ID: "diff1"}], [{ID: "diff2"}, {ID: "diff3"}]],
            COL_URLS_RESULTS: [
                [{"was_success": True, "status_code": 200, "error": None}]
            ]
            * 2,
        }
    )


@pytest.fixture
def df_urls_fail() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_URL_ORIGINAL: ["url5", "url6", "url7"],
            COL_URL_SUCCESS: [EMPTY_ACTEUR_FIELD] * 3,
            COL_ACTEURS: [
                [{ID: "a8"}],
                [{ID: "a9"}],
                [{ID: "a10"}, {ID: "a11"}, {ID: "a12"}],
            ],
            COL_URLS_RESULTS: [
                [{"was_success": False, "status_code": 404, "error": "error"}]
            ]
            * 3,
        }
    )


@pytest.fixture
def df_all_suggestions(
    df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail
) -> pd.DataFrame:
    return pd.concat(
        [df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail],
        ignore_index=True,
    )


def acteurs_create(dfs: list[pd.DataFrame]) -> None:
    df = pd.concat(dfs, ignore_index=True)
    for _, row in df.iterrows():
        for acteur in row[COL_ACTEURS]:
            RevisionActeurFactory(identifiant_unique=acteur[ID])
