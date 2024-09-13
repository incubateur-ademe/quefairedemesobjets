from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest

from dags.create_final_actors import (
    apply_corrections_acteur,
    merge_acteur_services,
    merge_labels,
)


@pytest.fixture
def df_load_acteur():
    return pd.DataFrame(
        {
            "identifiant_unique": ["actor1", "actor2"],
            "name": ["John Doe", "Jane Doe"],
            "cree_le": ["2022-01-01", "2022-01-02"],
        }
    )


@pytest.fixture
def df_load_revisionacteur():
    return pd.DataFrame(
        {
            "identifiant_unique": ["actor1"],
            "name": ["John Smith"],
            "cree_le": ["2022-01-03"],
        }
    )


class TestApplyCorrections:
    def test_apply_corrections_acteur(self, df_load_acteur, df_load_revisionacteur):

        # Mock the xcom_pull method
        mock_ti = Mock()

        def xcom_pull_side_effect(task_ids=""):
            if task_ids == "load_acteur":
                return df_load_acteur
            elif task_ids == "load_revisionacteur":
                return df_load_revisionacteur

        mock_ti.xcom_pull.side_effect = xcom_pull_side_effect

        # Call the function with the mocked ti
        result = apply_corrections_acteur(ti=mock_ti)

        # Check that the result is as expected
        expected = pd.DataFrame(
            {
                "identifiant_unique": ["actor1", "actor2"],
                "name": ["John Smith", "Jane Doe"],
                "cree_le": ["2022-01-01", "2022-01-02"],
            }
        )

        pd.testing.assert_frame_equal(result, expected)


class TestMergeLabels:
    @pytest.mark.parametrize(
        "load_acteur_labels, load_revisionacteur_labels, expected",
        [
            (
                pd.DataFrame(columns=["id", "acteur_id", "labelqualite_id"]),
                pd.DataFrame(columns=["id", "revisionacteur_id", "labelqualite_id"]),
                pd.DataFrame(columns=["displayedacteur_id", "labelqualite_id"]),
            ),
            (
                pd.DataFrame(columns=["id", "acteur_id", "labelqualite_id"]),
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "revisionacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                ),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "labelqualite_id"]),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                ),
                pd.DataFrame(
                    {
                        "id": [2],
                        "revisionacteur_id": ["actor2"],
                        "labelqualite_id": [1],
                    },
                ),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 1],
                    },
                    dtype=object,
                ),
            ),
        ],
    )
    def test_merge_labels(
        self, load_acteur_labels, load_revisionacteur_labels, expected
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_acteur_labels": load_acteur_labels,
            "load_revisionacteur_labels": load_revisionacteur_labels,
        }[task_ids]

        result = merge_labels(ti=mock)
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )


class TestMergeActeurServices:
    @pytest.mark.parametrize(
        "load_acteur_acteur_services, load_revisionacteur_acteur_services, expected",
        [
            (
                pd.DataFrame(columns=["id", "acteur_id", "acteurservice_id"]),
                pd.DataFrame(columns=["id", "revisionacteur_id", "acteurservice_id"]),
                pd.DataFrame(columns=["displayedacteur_id", "acteurservice_id"]),
            ),
            (
                pd.DataFrame(columns=["id", "acteur_id", "acteurservice_id"]),
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "revisionacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                ),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "acteurservice_id"]),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                ),
                pd.DataFrame(
                    {
                        "id": [2],
                        "revisionacteur_id": ["actor2"],
                        "acteurservice_id": [1],
                    },
                ),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 1],
                    },
                    dtype=object,
                ),
            ),
        ],
    )
    def test_merge_acteur_services(
        self, load_acteur_acteur_services, load_revisionacteur_acteur_services, expected
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_acteur_acteur_services": load_acteur_acteur_services,
            "load_revisionacteur_acteur_services": load_revisionacteur_acteur_services,
        }[task_ids]

        result = merge_acteur_services(ti=mock)
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )
