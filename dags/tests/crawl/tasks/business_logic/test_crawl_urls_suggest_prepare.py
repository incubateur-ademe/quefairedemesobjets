import pandas as pd
import pytest
from crawl.fixtures import acteurs_create, df_syntax_fail  # noqa
from core.models.constants import EMPTY_ACTEUR_FIELD

from dags.crawl.config.cohorts import COHORTS
from dags.crawl.config.columns import COLS
from dags.crawl.tasks.business_logic.crawl_urls_suggest import suggestions_prepare
from utils import logging_utils as log


@pytest.mark.django_db
class TestCrawlUrlsSuggestionsPepare:

    @pytest.fixture(autouse=True)
    def acteurs(self, df_syntax_fail):  # noqa
        # Creating acteurs is needed because suggestions_prepare
        # checks for acteur presence
        acteurs_create([df_syntax_fail])

    @pytest.fixture
    def suggestions(self, df_syntax_fail) -> list[dict]:  # noqa
        return suggestions_prepare(df=df_syntax_fail)

    def test_one_suggestion_per_url(self, suggestions, df_syntax_fail):  # noqa
        assert len(suggestions) == len(df_syntax_fail)

    def test_json_serializable(self, suggestions):
        log.json_dumps(suggestions)
        pass

    def test_raise_if_acteurs_missing(self):

        df = pd.DataFrame(
            {
                COLS.URL_ORIGIN: ["NA"],
                COLS.CRAWL_URL_SUCCESS: [EMPTY_ACTEUR_FIELD],
                COLS.ACTEURS: [[{COLS.ID: "ACTEUR NOT FOUND"}]],
                COLS.URLS_RESULTS: [None],
                COLS.COHORT: [COHORTS.SYNTAX_FAIL],
                COLS.SUGGEST_VALUE: [EMPTY_ACTEUR_FIELD],
            }
        )
        with pytest.raises(ValueError):
            suggestions_prepare(df=df)
