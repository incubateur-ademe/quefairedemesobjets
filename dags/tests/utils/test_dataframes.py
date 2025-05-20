import numpy as np
import pandas as pd
import pytest

from utils.dataframes import (
    df_add_original_columns,
    df_col_assert_get_unique,
    df_discard_if_col_vals_frequent,
    df_sort,
    df_split_on_filter,
)


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


class TestDfColAssertGetUnique:

    def test_col_is_unique(self):
        df = pd.DataFrame({"foo": ["a", "a"]})
        assert df_col_assert_get_unique(df, "foo") == "a"

    @pytest.mark.parametrize(
        "values",
        [
            ["a", "b"],
            ["a", ""],
            ["a", None],
            ["a", np.nan],
        ],
    )
    def test_raise_if_not_unique(self, values):
        df = pd.DataFrame({"foo": values})
        with pytest.raises(ValueError, match="doit être unique"):
            df_col_assert_get_unique(df, "foo")


class TestDfSplitOnFilter:

    @pytest.mark.parametrize(
        "input,dfa_values,dfb_values",
        [
            (["a1", "b", "a2"], ["a1", "a2"], ["b"]),
            # Cases were either dfa or dfb becomes
            # empty as a result of filter grabbing all
            (["a1", "a2"], ["a1", "a2"], []),
            (["b1", "b2"], [], ["b1", "b2"]),
        ],
    )
    def test_split_on_filter(self, input, dfa_values, dfb_values):
        df = pd.DataFrame({"foo": input})
        dfa, dfb = df_split_on_filter(df, df["foo"].str.contains("a"))
        assert dfa["foo"].tolist() == dfa_values
        assert dfb["foo"].tolist() == dfb_values

    def test_results_are_copies_not_views(self):
        # Silly but so easy to forget a .copy() and
        # have problems later down the pipeline
        df = pd.DataFrame({"foo": ["a"]})
        dfa, dfb = df_split_on_filter(df, df["foo"].str.contains("a"))
        assert not dfa._is_view  # type: ignore
        assert not dfb._is_view  # type: ignore


class TestDfDiscardIfColValuesTooFrequent:

    def test_df_discard_if_col_vals_frequent(self):
        df = pd.DataFrame({"foo": ["a", "a", "b", "b", "b", "c"]})
        df, df_discarded = df_discard_if_col_vals_frequent(df, "foo", 3)
        assert df["foo"].tolist() == ["a", "a", "c"]
        assert df_discarded["foo"].tolist() == ["b", "b", "b"]


class TestDfAddOriginalColumns:

    def test_df_add_original_df_columns(self):
        df_clusters = pd.DataFrame(
            {
                "identifiant_unique": ["1", "3"],
                "cluster_id": ["c1", "c1"],
                "colonne_cluster": ["v1", "v3"],
            }
        )

        df_original = pd.DataFrame(
            {
                "identifiant_unique": ["1", "2", "3", "4"],
                "colonne_original": ["foo", "foo", "bar", "bar"],
            }
        )
        df = df_add_original_columns(df_modify=df_clusters, df_original=df_original)
        assert df.shape == (2, 4)
        assert df["identifiant_unique"].tolist() == ["1", "3"]
        assert df["cluster_id"].tolist() == ["c1", "c1"]
        assert df["colonne_cluster"].tolist() == ["v1", "v3"]
        assert df["colonne_original"].tolist() == ["foo", "bar"]
