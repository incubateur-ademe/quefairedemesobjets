import pandas as pd
import pytest

from dags.utils.dataframes import df_sort


class TestDfSort:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                "not_mentioned_in_params": [None, None, None],
                "sort_rows1": ["a", "b", "a"],
                "sort_rows3": ["a3", "b", "a1"],
                "sort_cols2": ["a", "b", "c"],
                "sort_cols3": ["d", "e", "f"],
            }
        )

    @pytest.fixture
    def df_sorted(self, df) -> pd.DataFrame:
        return df_sort(
            df,
            sort_rows=["sort_rows1", "sort_rows2", "sort_rows3"],
            sort_cols=["sort_cols1", "sort_cols3", "sort_cols2"],
        )

    def test_no_column_is_lost(self, df, df_sorted):
        # Even though not_mentioned_in_params is not
        # in any of the cols params
        assert set(df.columns) == set(df_sorted.columns)

    def test_sort_rows(self, df_sorted):
        # We sort by ascending order of given columns
        # if present, we don't crash if some are missing
        assert df_sorted[["sort_rows1", "sort_rows3"]].values.tolist() == [
            ["a", "a1"],
            ["a", "a3"],
            ["b", "b"],
        ]

    def test_sort_cols(self, df_sorted):
        # We prioritize given columns, don't crash on missing
        # and then add the rest
        assert df_sorted.columns.tolist() == [
            "sort_cols3",
            "sort_cols2",
            "not_mentioned_in_params",
            "sort_rows1",
            "sort_rows3",
        ]
