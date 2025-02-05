import pandas as pd
import pytest
from cluster.tasks.business_logic import cluster_acteurs_parent_calculations


class TestClusterActeursParentCalculations:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                "id": [
                    "p1",
                    "enfant_p1",
                    "p2",
                    "enfant_p2",
                    "enfant_p2",
                ],
                "parent_id": [None, "p1", None, "p2", "p2"],
            }
        )

    @pytest.fixture
    def df_calc(self, df):
        return cluster_acteurs_parent_calculations(df)

    def test_column_added_is_parent_current(self, df_calc):
        assert "is_parent_current" in df_calc.columns

    def test_column_added_children_count(self, df_calc):
        assert "children_count" in df_calc.columns

    def test_calculation_correct_is_parent_current(self, df_calc):
        assert df_calc["is_parent_current"].tolist() == [
            True,
            False,
            True,
            False,
            False,
        ]

    def test_calculation_correct_children_count(self, df_calc):
        assert df_calc["children_count"].tolist() == [1, 0, 2, 0, 0]
