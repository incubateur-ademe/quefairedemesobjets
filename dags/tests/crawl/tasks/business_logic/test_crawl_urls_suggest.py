import pandas as pd
import pytest

# TODO: hinting complaining about below not being used,
# how to fix properly via pytest conf?
from crawl.fixtures import acteurs_create, df_syntax_fail  # noqa
from crawl.tasks.business_logic.crawl_urls_suggest import crawl_urls_suggest

from dags.crawl.config.columns import COLS


@pytest.mark.django_db
class TestCrawlUrlsSuggest:

    @pytest.fixture(autouse=True)
    def acteurs(self, df_syntax_fail):  # noqa
        acteurs_create([df_syntax_fail])

    @pytest.mark.parametrize(
        "dry_run,db_cnt_cohort,db_cnt_sugg",
        [
            (True, 0, 0),
            (False, 1, 2),
        ],
    )
    def test_dry_run_on_off(
        self, df_syntax_fail, dry_run, db_cnt_cohort, db_cnt_sugg  # noqa
    ):
        from data.models.suggestion import Suggestion, SuggestionCohorte

        written_to_db_count = crawl_urls_suggest(
            df=df_syntax_fail,
            dry_run=dry_run,
            dag_display_name=f"test_crawl_urls_action_{dry_run=}",
            run_id=f"test_crawl_urls_execution_{dry_run=}",
        )
        assert written_to_db_count == db_cnt_sugg
        assert SuggestionCohorte.objects.count() == db_cnt_cohort
        assert Suggestion.objects.count() == db_cnt_sugg

    def test_raise_if_df_none_or_empty(self):
        with pytest.raises(ValueError, match="DF vide ou None"):
            crawl_urls_suggest(df=None, dry_run=True, dag_display_name="a", run_id="b")

    def test_raise_if_multiple_cohorts(self):
        df = pd.DataFrame({COLS.COHORT: ["a", "b"]})
        with pytest.raises(ValueError, match=f"Colonne {COLS.COHORT} doit être unique"):
            crawl_urls_suggest(df=df, dry_run=True, dag_display_name="a", run_id="b")
