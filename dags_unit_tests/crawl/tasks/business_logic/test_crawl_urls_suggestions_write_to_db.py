import pytest

# TODO: hinting complaining about below not being used,
# how to fix properly via pytest conf?
from crawl.fixtures import (  # noqa
    acteurs_create,
    df_all_suggestions,
    df_dns_fail,
    df_syntax_fail,
    df_urls_fail,
    df_urls_ok_diff,
)

from dags.crawl.tasks.business_logic.crawl_urls_suggestions_metadata import (
    crawl_urls_suggestions_metadata,
)
from dags.crawl.tasks.business_logic.crawl_urls_suggestions_prepare import (
    crawl_urls_suggestions_prepare,
)
from dags.crawl.tasks.business_logic.crawl_urls_suggestions_to_db import (
    crawl_urls_suggestions_to_db,
)


@pytest.mark.django_db
class TestCrawlUrlsSuggestionsWriteToDb:

    @pytest.fixture(autouse=True)
    def acteurs(
        self, df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail  # noqa
    ):
        acteurs_create([df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail])

    def test_crawl_urls_suggestions_to_db(
        self,
        df_syntax_fail,  # noqa
        df_dns_fail,  # noqa
        df_urls_ok_diff,  # noqa
        df_urls_fail,  # noqa
        df_all_suggestions,  # noqa
    ):
        from data.models.suggestion import Suggestion, SuggestionCohorte

        metadata = crawl_urls_suggestions_metadata(
            df_syntax_fail=df_syntax_fail,
            df_dns_fail=df_dns_fail,
            df_urls_ok_diff=df_urls_ok_diff,
            df_urls_fail=df_urls_fail,
        )
        suggestions = crawl_urls_suggestions_prepare(
            df_syntax_fail=df_syntax_fail,
            df_dns_fail=df_dns_fail,
            df_urls_ok_diff=df_urls_ok_diff,
            df_urls_fail=df_urls_fail,
        )
        crawl_urls_suggestions_to_db(
            metadata=metadata,  # type: ignore
            suggestions=suggestions,
            identifiant_action="test_crawl_urls_action",
            identifiant_execution="test_crawl_urls_execution",
        )

        cohorte = SuggestionCohorte.objects.get(
            identifiant_action="test_crawl_urls_action",
            identifiant_execution="test_crawl_urls_execution",
        )

        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohorte)
        assert suggestions.count() == len(df_all_suggestions)
