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
def df_ok_same() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_URL_ORIGINAL: ["https://good.com"],
            COL_URL_SUCCESS: ["https://good.com"],
            COL_ACTEURS: [[{ID: "a1"}, {ID: "a2"}, {ID: "a3"}]],
            COL_URLS_RESULTS: [
                [{"was_success": True, "status_code": 200, "error": None}]
            ],
        }
    )


@pytest.fixture
def df_ok_diff() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_URL_ORIGINAL: ["http://a.com", "http://b.com"],
            COL_URL_SUCCESS: ["https://a.com", "https://b.com"],
            COL_ACTEURS: [[{ID: "a5"}], [{ID: "a6"}, {ID: "a7"}]],
            COL_URLS_RESULTS: [
                [{"was_success": True, "status_code": 200, "error": None}]
            ]
            * 2,
        }
    )


@pytest.fixture
def df_fail() -> pd.DataFrame:
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


def acteurs_create(dfs: list[pd.DataFrame]) -> None:
    df = pd.concat(dfs, ignore_index=True)
    for _, row in df.iterrows():
        for acteur in row[COL_ACTEURS]:
            RevisionActeurFactory(identifiant_unique=acteur[ID])
