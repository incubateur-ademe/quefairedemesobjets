import pytest

# TODO: hinting complaining about below not being used,
# how to fix properly via pytest conf?
from crawl.fixtures import acteurs_create, df_fail, df_ok_diff, df_ok_same  # noqa
from crawl.tasks.business_logic.suggestions.metadata import (
    crawl_urls_suggestions_metadata,
)
from crawl.tasks.business_logic.suggestions.prepare import (
    crawl_urls_suggestions_prepare,
)
from crawl.tasks.business_logic.suggestions.write_to_db import (
    crawl_urls_suggestions_write_to_db,
)


@pytest.mark.django_db
class TestCrawlUrlsSuggestionsWriteToDb:

    @pytest.fixture(autouse=True)
    def acteurs(self, df_ok_same, df_ok_diff, df_fail):  # noqa
        acteurs_create([df_ok_same, df_ok_diff, df_fail])

    def test_crawl_urls_suggestions_write_to_dbs(
        self, df_ok_same, df_ok_diff, df_fail  # noqa
    ):
        metadata = crawl_urls_suggestions_metadata(
            df_ok_same=df_ok_same,
            df_ok_diff=df_ok_diff,
            df_fail=df_fail,
        )

        suggestions = crawl_urls_suggestions_prepare(df_ok_diff, df_fail)
        crawl_urls_suggestions_write_to_db(
            metadata=metadata,
            suggestions=suggestions,
            identifiant_action="mon_action",
            identifiant_execution="mon_execution",
        )
