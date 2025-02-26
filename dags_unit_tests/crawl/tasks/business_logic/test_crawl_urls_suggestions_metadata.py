import pandas as pd
import pytest
from crawl.fixtures import (  # noqa
    df_all_suggestions,
    df_dns_fail,
    df_syntax_fail,
    df_urls_fail,
    df_urls_ok_diff,
)

from dags.crawl.config.constants import (
    SCENARIO_DNS_FAIL,
    SCENARIO_SYNTAX_FAIL,
    SCENARIO_TOTAL,
    SCENARIO_URL_FAIL,
    SCENARIO_URL_OK_DIFF,
)
from dags.crawl.tasks.business_logic.crawl_urls_suggestions_metadata import (
    crawl_urls_suggestions_metadata,
)
from dags.utils import logging_utils as log


class TestCrawlUrlsSuggestionsMetadata:

    @pytest.fixture
    def metadata(
        self, df_syntax_fail, df_dns_fail, df_urls_ok_diff, df_urls_fail  # noqa
    ):
        return crawl_urls_suggestions_metadata(
            df_syntax_fail=df_syntax_fail,
            df_dns_fail=df_dns_fail,
            df_urls_ok_diff=df_urls_ok_diff,
            df_urls_fail=df_urls_fail,
        )

    def test_syntax_fail(self, metadata, df_syntax_fail):  # noqa
        values = [v for k, v in metadata.items() if k.startswith(SCENARIO_SYNTAX_FAIL)]
        assert values[0] == len(df_syntax_fail)
        assert values[1] == int(df_syntax_fail["acteurs"].apply(len).sum())

    def test_dns_fail(self, metadata, df_dns_fail):  # noqa
        values = [v for k, v in metadata.items() if k.startswith(SCENARIO_DNS_FAIL)]
        assert values[0] == len(df_dns_fail)
        assert values[1] == int(df_dns_fail["acteurs"].apply(len).sum())

    def test_urls_ok_diff(self, metadata, df_urls_ok_diff):  # noqa
        values = [v for k, v in metadata.items() if k.startswith(SCENARIO_URL_OK_DIFF)]
        assert values[0] == len(df_urls_ok_diff)
        assert values[1] == int(df_urls_ok_diff["acteurs"].apply(len).sum())

    def test_urls_fail(self, metadata, df_urls_fail):  # noqa
        values = [v for k, v in metadata.items() if k.startswith(SCENARIO_URL_FAIL)]
        assert values[0] == len(df_urls_fail)
        assert values[1] == int(df_urls_fail["acteurs"].apply(len).sum())

    def test_total(self, metadata, df_all_suggestions):  # noqa
        values = [v for k, v in metadata.items() if k.startswith(SCENARIO_TOTAL)]
        assert values[0] == len(df_all_suggestions)
        assert values[1] == int(df_all_suggestions["acteurs"].apply(len).sum())

    def test_metadata_is_json_serializable(self, metadata):
        log.json_dumps(metadata)
        pass

    @pytest.mark.parametrize(
        ("input"),
        [None, pd.DataFrame()],
    )
    def test_returns_none_if_all_none(self, input):
        """Since there are 4 different dataframes
        coming from 4 different tasks, instead of
        having to manage complex task dependencies at
        airflow task definition level, we always run
        the metadata task passing all dfs and return None
        if there are no suggestions to be made"""
        assert (
            crawl_urls_suggestions_metadata(
                df_syntax_fail=input,  # type: ignore
                df_dns_fail=input,  # type: ignore
                df_urls_ok_diff=input,  # type: ignore
                df_urls_fail=input,  # type: ignore
            )
            is None
        )

    def test_partial_empty(self, df_syntax_fail, df_urls_fail):  # noqa
        """If some of the dataframes are empty, we still
        want to return metadata for the non-empty ones"""
        metadata: dict[str, int] = crawl_urls_suggestions_metadata(
            df_syntax_fail=df_syntax_fail,
            df_dns_fail=None,  # type: ignore
            df_urls_ok_diff=None,  # type: ignore
            df_urls_fail=df_urls_fail,
        )  # type: ignore
        # Only given scenarios are set
        df_comb = pd.concat([df_syntax_fail, df_urls_fail], ignore_index=True)
        assert all(not k.startswith(SCENARIO_DNS_FAIL) for k in metadata.keys())
        assert all(not k.startswith(SCENARIO_URL_OK_DIFF) for k in metadata.keys())
        assert metadata[SCENARIO_TOTAL + ": # URLs"] == len(df_comb)
        assert metadata[SCENARIO_TOTAL + ": # Acteurs"] == int(
            df_comb["acteurs"].apply(len).sum()
        )
