import pytest
from crawl.fixtures import df_fail, df_ok_diff, df_ok_same  # noqa

from dags.crawl.tasks.business_logic.suggestions.metadata import (
    crawl_urls_suggestions_metadata,
)
from dags.utils import logging_utils as log


class TestCrawlUrlsSuggestionsMetadata:

    @pytest.fixture
    def metadata(self, df_ok_same, df_ok_diff, df_fail):  # noqa
        return crawl_urls_suggestions_metadata(df_ok_same, df_ok_diff, df_fail)

    def test_ok_same(self, metadata):
        assert metadata["🟢 Succès ET inchangés: URLs"] == 1
        assert metadata["🟢 Succès ET inchangés: acteurs"] == 3

    def test_ok_diff(self, metadata):
        assert metadata["🟡 Succès ET différents: URLs"] == 2
        assert metadata["🟡 Succès ET différents: acteurs"] == 3

    def test_fail(self, metadata):
        assert metadata["🔴 Échec: URLs"] == 3
        assert metadata["🔴 Échec: acteurs"] == 5

    def test_metadata_is_json_serializable(self, metadata):
        log.json_dumps(metadata)
        pass
