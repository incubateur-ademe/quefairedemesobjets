import pytest
from crawl.config.constants import SCENARIO_FAIL, SCENARIO_OK_DIFF
from crawl.fixtures import acteurs_create, df_fail, df_ok_diff  # noqa
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD

from dags.crawl.tasks.business_logic.suggestions.prepare import (
    crawl_urls_suggestions_prepare,
)
from dags.utils import logging_utils as log

ID = "identifiant_unique"


@pytest.mark.django_db
class TestCrawlUrlsSuggestionsPepare:

    @pytest.fixture(autouse=True)
    def acteurs(self, df_ok_diff, df_fail):  # noqa
        acteurs_create([df_ok_diff, df_fail])

    @pytest.fixture
    def prepare(self, df_ok_diff, df_fail) -> list[dict]:  # noqa
        suggestions = crawl_urls_suggestions_prepare(df_ok_diff, df_fail)
        return suggestions

    def test_total_suggestions(self, prepare):
        assert len(prepare) == 5

    def test_ok_diff(self, prepare):
        ok = prepare[:2]
        assert all(x["contexte"]["Scénario"] == SCENARIO_OK_DIFF for x in ok)
        assert [x["contexte"]["URL proposée"] for x in ok] == [
            "https://a.com",
            "https://b.com",
        ]
        assert all("scenario" in x["suggestion"] for x in ok)
        assert all("reason" in x["suggestion"] for x in ok)
        assert all("url_original" in x["suggestion"] for x in ok)
        assert all("url_proposed" in x["suggestion"] for x in ok)
        assert all("changes" in x["suggestion"] for x in ok)

    def test_fail(self, prepare):
        fail = prepare[-3:]
        assert all(x["contexte"]["Scénario"] == SCENARIO_FAIL for x in fail)
        assert [x["contexte"]["URL proposée"] for x in fail] == [
            EMPTY_ACTEUR_FIELD,
            EMPTY_ACTEUR_FIELD,
            EMPTY_ACTEUR_FIELD,
        ]

    def test_prepare_is_json_serializable(self, prepare):
        log.json_dumps(prepare)
        pass
