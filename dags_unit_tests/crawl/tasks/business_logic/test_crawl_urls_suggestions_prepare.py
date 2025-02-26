import pandas as pd
import pytest
from crawl.fixtures import (  # noqa
    acteurs_create,
    df_dns_fail,
    df_syntax_fail,
    df_urls_fail,
    df_urls_ok_diff,
)

from dags.crawl.config.constants import (
    SCENARIO_DNS_FAIL,
    SCENARIO_SYNTAX_FAIL,
    SCENARIO_URL_FAIL,
    SCENARIO_URL_OK_DIFF,
)
from dags.crawl.tasks.business_logic.crawl_urls_suggestions_prepare import (
    crawl_urls_suggestions_prepare,
)
from dags.utils import logging_utils as log

ID = "identifiant_unique"


@pytest.mark.django_db
class TestCrawlUrlsSuggestionsPepare:

    @pytest.fixture(autouse=True)
    def acteurs(
        self, df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail  # noqa
    ):
        acteurs_create([df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail])

    @pytest.fixture
    def suggestions(
        self, df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail  # noqa
    ) -> list[dict] | None:
        return crawl_urls_suggestions_prepare(
            df_syntax_fail=df_syntax_fail,
            df_dns_fail=df_dns_fail,
            df_urls_ok_diff=df_urls_ok_diff,
            df_urls_fail=df_urls_fail,
        )

    @pytest.fixture
    def sdata(self, suggestions):
        # Our suggestion model is a bit repetitive in naming
        # as we have Suggestion.suggestion (instead of e.g. Suggestion.changes)
        return [x["suggestion"] for x in suggestions]

    def test_syntax_fail(self, sdata, df_syntax_fail):  # noqa
        subset = [x for x in sdata if x["scenario"] == SCENARIO_SYNTAX_FAIL]
        assert len(subset) == len(df_syntax_fail)

    def test_dns_fail(self, sdata, df_dns_fail):  # noqa
        subset = [x for x in sdata if x["scenario"] == SCENARIO_DNS_FAIL]
        assert len(subset) == len(df_dns_fail)

    def test_urls_ok_diff(self, sdata, df_urls_ok_diff):  # noqa
        subset = [x for x in sdata if x["scenario"] == SCENARIO_URL_OK_DIFF]
        assert len(subset) == len(df_urls_ok_diff)

    def test_urls_fail(self, sdata, df_urls_fail):  # noqa
        subset = [x for x in sdata if x["scenario"] == SCENARIO_URL_FAIL]
        assert len(subset) == len(df_urls_fail)

    def test_suggestions_are_json_serializable(self, suggestions):
        log.json_dumps(suggestions)
        pass

    def test_raise_if_no_suggestions(self):
        """We should never reach the suggestions_prepare step
        as the previous suggestions_metadata step should return
        None to skip, so we ensure we raise exceptions if no
        suggestions are available"""
        with pytest.raises(ValueError):
            crawl_urls_suggestions_prepare(
                df_syntax_fail=pd.DataFrame(),
                df_dns_fail=pd.DataFrame(),
                df_urls_ok_diff=pd.DataFrame(),
                df_urls_fail=pd.DataFrame(),
            )
