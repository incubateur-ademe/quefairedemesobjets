from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from create_final_actors import (
    apply_corrections_acteur,
    merge_acteur_services,
    merge_labels,
)


class TestApplyCorrections:

    @pytest.fixture
    def df_load_acteur(self):
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
    def df_load_revisionacteur(self):
        return pd.DataFrame(
            {
                "identifiant_unique": ["actor1"],
                "name": ["John Smith"],
                "cree_le": ["2022-01-03"],
                "parent_id": [None],
                "source_id": [1],
            }
        )

    def test_apply_corrections_acteur(self, df_load_acteur, df_load_revisionacteur):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_acteur": df_load_acteur,
            "load_revisionacteur": df_load_revisionacteur,
        }[task_ids]

        # Call the function with the mocked ti
        result = apply_corrections_acteur(ti=mock)

        # Check that the result is as expected
        df_acteur_expected = pd.DataFrame(
            {
                "identifiant_unique": ["actor1", "actor2"],
                "name": ["John Smith", "Jane Doe"],
                "cree_le": ["2022-01-01", "2022-01-02"],
                "parent_id": [None, None],
                "source_id": [1, 2],
                "uuid": ["Hogy2rqwtvgMUctiqUyYmH", "AS5wKPytvs9VjWEFQdqTwK"],
            }
        )
        df_children_expected = pd.DataFrame(
            columns=["parent_id", "identifiant_unique", "source_id"]
        )
        df_children_expected = df_children_expected.astype(
            {
                "parent_id": object,
                "identifiant_unique": object,
                "source_id": int,
            }
        )

        pd.testing.assert_frame_equal(
            result["df_acteur_merged"].drop(columns=["uuid"]), df_acteur_expected
        )
        pd.testing.assert_frame_equal(result["df_children"], df_children_expected)

    @pytest.fixture
    def df_load_acteur_with_children(self):
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
    def df_load_revisionacteur_with_children(self):
        return pd.DataFrame(
            {
                "identifiant_unique": ["actor1", "actor2", "actor3"],
                "name": ["John Doe", "Jane Doe", "Jane Doe"],
                "cree_le": ["2022-01-03", "2022-01-03", "2022-01-03"],
                "parent_id": ["actor3", "actor3", None],
                "source_id": [1, 2, None],
            }
        )

    def test_apply_corrections_acteur_children(
        self, df_load_acteur_with_children, df_load_revisionacteur_with_children
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_acteur": df_load_acteur_with_children,
            "load_revisionacteur": df_load_revisionacteur_with_children,
        }[task_ids]

        # Call the function with the mocked ti
        result = apply_corrections_acteur(ti=mock)

        # Check that the result is as expected
        df_acteur_expected = pd.DataFrame(
            {
                "identifiant_unique": ["actor3"],
                "name": ["Jane Doe"],
                "cree_le": ["2022-01-03"],
                "parent_id": [None],
                "source_id": [np.nan],
                "uuid": ["Ad4fYCpSxc7rpzNvK8wCYr"],
            }
        )
        df_children_expected = pd.DataFrame(
            {
                "parent_id": ["actor3", "actor3"],
                "identifiant_unique": ["actor1", "actor2"],
                # le merge cast en float car il existe des valeur nulles
                "source_id": [1.0, 2.0],
            }
        )

        pd.testing.assert_frame_equal(
            result["df_acteur_merged"].reset_index(drop=True).drop(columns=["uuid"]),
            df_acteur_expected.reset_index(drop=True),
        )
        pd.testing.assert_frame_equal(
            result["df_children"].reset_index(drop=True),
            df_children_expected.reset_index(drop=True),
        )


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
