from unittest.mock import Mock

import pandas as pd
import pytest

from dags.create_final_actors import apply_corrections


@pytest.fixture
def df_load_actors():
    return pd.DataFrame(
        {
            "identifiant_unique": ["actor1", "actor2"],
            "name": ["John Doe", "Jane Doe"],
            "cree_le": ["2022-01-01", "2022-01-02"],
        }
    )


@pytest.fixture
def df_load_revision_actors():
    return pd.DataFrame(
        {
            "identifiant_unique": ["actor1"],
            "name": ["John Smith"],
            "cree_le": ["2022-01-03"],
        }
    )


class TestApplyCorrections:
    def test_apply_corrections(self, df_load_actors, df_load_revision_actors):

        # Mock the xcom_pull method
        mock_ti = Mock()

        def xcom_pull_side_effect(task_ids=""):
            if task_ids == "load_actors":
                return df_load_actors
            elif task_ids == "load_revision_actors":
                return df_load_revision_actors

        mock_ti.xcom_pull.side_effect = xcom_pull_side_effect

        # Call the function with the mocked ti
        result = apply_corrections(ti=mock_ti)

        # Check that the result is as expected
        expected = pd.DataFrame(
            {
                "identifiant_unique": ["actor1", "actor2"],
                "name": ["John Smith", "Jane Doe"],
                "cree_le": ["2022-01-01", "2022-01-02"],
            }
        )

        pd.testing.assert_frame_equal(result, expected)
