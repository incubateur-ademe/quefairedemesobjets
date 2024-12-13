import numpy as np
import pandas as pd
import pytest
from compute_acteurs.tasks.business_logic.apply_corrections_acteur import (
    apply_corrections_acteur,
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

        # Call the function with the mocked ti
        result = apply_corrections_acteur(
            df_acteur=df_load_acteur, df_revisionacteur=df_load_revisionacteur
        )

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

        pd.testing.assert_frame_equal(result["df_acteur_merged"], df_acteur_expected)
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
        # Call the function with the mocked ti
        result = apply_corrections_acteur(
            df_acteur=df_load_acteur_with_children,
            df_revisionacteur=df_load_revisionacteur_with_children,
        )

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
            result["df_acteur_merged"].reset_index(drop=True),
            df_acteur_expected.reset_index(drop=True),
        )
        pd.testing.assert_frame_equal(
            result["df_children"].reset_index(drop=True),
            df_children_expected.reset_index(drop=True),
        )
