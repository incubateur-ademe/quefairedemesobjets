from unittest.mock import MagicMock

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
            "parent_id": [None, None],
            "source_id": [1, 2],
        }
    )


@pytest.fixture
def df_load_revisionacteur():
    return pd.DataFrame(
        {
            "identifiant_unique": ["actor1"],
            "name": ["John Smith"],
            "cree_le": ["2022-01-03"],
            "parent_id": [None],
            "source_id": [1],
        }
    )


class TestApplyCorrections:
    def test_apply_corrections_acteur(self, df_load_acteur, df_load_revisionacteur):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_acteur": df_load_acteur,
            "load_revisionacteur": df_load_revisionacteur,
        }[task_ids]

        # Call the function with the mocked ti
        result = apply_corrections_acteur(ti=mock)

        # Check that the result is as expected
        expected = pd.DataFrame(
            {
                "identifiant_unique": ["actor1", "actor2"],
                "name": ["John Smith", "Jane Doe"],
                "cree_le": ["2022-01-01", "2022-01-02"],
                "parent_id": [None, None],
                "source_id": [1, 2],
            }
        )

        pd.testing.assert_frame_equal(result["df_displayed_actors"], expected)


class TestMergeLabels:
    @pytest.mark.parametrize(
        "load_acteur_labels, load_revisionacteur_labels, load_revisionacteur, expected",
        [
            (
                pd.DataFrame(columns=["id", "acteur_id", "labelqualite_id"]),
                pd.DataFrame(columns=["id", "revisionacteur_id", "labelqualite_id"]),
                pd.DataFrame(columns=["identifiant_unique"]),
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
                pd.DataFrame({"identifiant_unique": ["actor1", "actor2"]}),
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
                pd.DataFrame(columns=["identifiant_unique"]),
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
                pd.DataFrame({"identifiant_unique": ["actor2"]}),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 1],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1],
                        "acteur_id": ["actor1"],
                        "labelqualite_id": [1],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "labelqualite_id"]),
                pd.DataFrame({"identifiant_unique": ["actor1"]}),
                pd.DataFrame(columns=["displayedacteur_id", "labelqualite_id"]),
            ),
        ],
    )
    def test_merge_labels(
        self,
        load_acteur_labels,
        load_revisionacteur_labels,
        load_revisionacteur,
        expected,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_acteur_labels": load_acteur_labels,
            "load_revisionacteur_labels": load_revisionacteur_labels,
            "load_revisionacteur": load_revisionacteur,
        }[task_ids]

        result = merge_labels(ti=mock)
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )


class TestMergeActeurServices:
    @pytest.mark.parametrize(
        "load_acteur_acteur_services, load_revisionacteur_acteur_services,"
        " load_revisionacteur, expected",
        [
            (
                pd.DataFrame(columns=["id", "acteur_id", "acteurservice_id"]),
                pd.DataFrame(columns=["id", "revisionacteur_id", "acteurservice_id"]),
                pd.DataFrame(columns=["identifiant_unique"]),
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
                pd.DataFrame({"identifiant_unique": ["actor1", "actor2"]}),
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
                pd.DataFrame(columns=["identifiant_unique"]),
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
                # pd.DataFrame({"identifiant_unique": ["actor2"]}),
                pd.DataFrame({"identifiant_unique": ["actor2"]}),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 1],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1],
                        "acteur_id": ["actor1"],
                        "acteurservice_id": [1],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "acteurservice_id"]),
                pd.DataFrame({"identifiant_unique": ["actor1"]}),
                pd.DataFrame(columns=["displayedacteur_id", "acteurservice_id"]),
            ),
        ],
    )
    def test_merge_acteur_services(
        self,
        load_acteur_acteur_services,
        load_revisionacteur_acteur_services,
        load_revisionacteur,
        expected,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_acteur_acteur_services": load_acteur_acteur_services,
            "load_revisionacteur_acteur_services": load_revisionacteur_acteur_services,
            "load_revisionacteur": load_revisionacteur,
        }[task_ids]

        result = merge_acteur_services(ti=mock)
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )
