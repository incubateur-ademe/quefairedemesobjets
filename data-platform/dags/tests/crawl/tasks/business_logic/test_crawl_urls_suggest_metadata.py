import pandas as pd
import pytest

from dags.crawl.config.cohorts import COHORTS
from dags.crawl.config.columns import COLS
from dags.crawl.tasks.business_logic.crawl_urls_suggest import suggestions_metadata
from utils import logging_utils as log


class TestCrawlUrlsSuggestionsMetadata:

    @pytest.fixture
    def df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                COLS.COHORT: [COHORTS.SYNTAX_FAIL] * 2,
                COLS.ACTEURS: [[{}, {}], [{}, {}, {}]],
            }
        )

    @pytest.fixture
    def metadata(self, df):
        return suggestions_metadata(df=df)

    def test_json_serializable(self, metadata):
        log.json_dumps(metadata)
        pass

    def test_metadata_content(self, metadata):
        assert metadata == {
            f"{COHORTS.SYNTAX_FAIL}: # URLs": 2,
            f"{COHORTS.SYNTAX_FAIL}: # Acteurs": 5,
        }
