import numpy as np
import pandas as pd
import pytest
from compute_acteurs.tasks.business_logic.compute_acteur import compute_acteur
from faker import Faker
from sources.config import shared_constants as constants


class TestApplyCorrections:

    @pytest.fixture
    def df_load_acteur(self):
        return pd.DataFrame(
            {
                "id": ["actor1", "actor2"],
                "name": ["John Doe", "Jane Doe"],
                "cree_le": ["2022-01-01", "2022-01-02"],
                "parent_id": [None, None],
                "source_id": [1, 2],
                "statut": ["ACTIF", "ACTIF"],
            }
        )

    @pytest.fixture
    def df_load_revisionacteur(self):
        return pd.DataFrame(
            {
                "id": ["actor1"],
                "name": ["John Smith"],
                "cree_le": ["2022-01-03"],
                "parent_id": [None],
                "source_id": [1],
                "statut": ["ACTIF"],
            }
        )

    def test_compute_acteur(self, df_load_acteur, df_load_revisionacteur):

        # Call the function with the mocked ti
        result = compute_acteur(
            df_acteur=df_load_acteur, df_revisionacteur=df_load_revisionacteur
        )

        # Check that the result is as expected
        df_acteur_expected = pd.DataFrame(
            {
                "id": ["actor1", "actor2"],
                "name": ["John Smith", "Jane Doe"],
                "cree_le": ["2022-01-01", "2022-01-02"],
                "parent_id": [None, None],
                "source_id": [1, 2],
                "statut": ["ACTIF", "ACTIF"],
                "uuid": ["Hogy2rqwtvgMUctiqUyYmH", "AS5wKPytvs9VjWEFQdqTwK"],
            }
        )
        df_children_expected = pd.DataFrame(columns=["parent_id", "id", "source_id"])
        df_children_expected = df_children_expected.astype(
            {
                "parent_id": object,
                "id": object,
                "source_id": int,
            }
        )

        pd.testing.assert_frame_equal(result["df_acteur_merged"], df_acteur_expected)
        pd.testing.assert_frame_equal(result["df_children"], df_children_expected)

    @pytest.fixture
    def df_load_acteur_with_children(self):
        return pd.DataFrame(
            {
                "id": ["actor1", "actor2"],
                "name": ["John Doe", "Jane Doe"],
                "cree_le": ["2022-01-01", "2022-01-02"],
                "parent_id": [None, None],
                "source_id": [1, 2],
                "statut": ["ACTIF", "ACTIF"],
            }
        )

    @pytest.fixture
    def df_load_revisionacteur_with_children(self):
        return pd.DataFrame(
            {
                "id": ["actor1", "actor2", "actor3"],
                "name": ["John Doe", "Jane Doe", "Jane Doe"],
                "cree_le": ["2022-01-03", "2022-01-03", "2022-01-03"],
                "parent_id": ["actor3", "actor3", None],
                "source_id": [1, 2, None],
                "statut": ["ACTIF", "ACTIF", "ACTIF"],
            }
        )

    def test_compute_acteur_children(
        self, df_load_acteur_with_children, df_load_revisionacteur_with_children
    ):
        # Call the function with the mocked ti
        result = compute_acteur(
            df_acteur=df_load_acteur_with_children,
            df_revisionacteur=df_load_revisionacteur_with_children,
        )

        # Check that the result is as expected
        df_acteur_expected = pd.DataFrame(
            {
                "id": ["actor3"],
                "name": ["Jane Doe"],
                "cree_le": ["2022-01-03"],
                "parent_id": [None],
                "source_id": [np.nan],
                "statut": ["ACTIF"],
                "uuid": ["Ad4fYCpSxc7rpzNvK8wCYr"],
            }
        )
        df_children_expected = pd.DataFrame(
            {
                "parent_id": ["actor3", "actor3"],
                "id": ["actor1", "actor2"],
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


faker = Faker()
CHARFIELDS = [
    "nom",
    "adresse",
    "adresse_complement",
    "code_postal",
    "ville",
    "url",
    "email",
    "telephone",
    "nom_commercial",
    "nom_officiel",
    "siren",
    "siret",
    "identifiant_externe",
    "naf_principal",
    "horaires_osm",
    "public_accueilli",
    "reprise",
    "description",
    "commentaires",
    "horaires_description",
]


class TestOverrideValues:
    def test_empty_value(self):
        acteur_fields = {}
        revisionacteur_fields = {}
        expected_fields = {}
        for field in CHARFIELDS:
            acteur_fields[field] = [faker.word()]
            revisionacteur_fields[field] = ["__empty__"]
            expected_fields[field] = [""]
        for field_list in [acteur_fields, revisionacteur_fields, expected_fields]:
            field_list["id"] = ["a1"]
            field_list["statut"] = [constants.ACTEUR_ACTIF]
            field_list["parent_id"] = [None]
            field_list["source_id"] = [1]
        df_acteur = pd.DataFrame(acteur_fields)
        df_revisionacteur = pd.DataFrame(revisionacteur_fields)
        df_expected = pd.DataFrame(expected_fields)
        df_result = compute_acteur(df_acteur, df_revisionacteur)["df_acteur_merged"]
        df_result.drop(columns=["uuid"], inplace=True)
        # Trier les colonnes avant de comparer
        df_result = df_result.sort_index(axis=1)
        df_expected = df_expected.sort_index(axis=1)
        pd.testing.assert_frame_equal(df_result, df_expected)

    def test_none_value(self):
        acteur_fields = {}
        revisionacteur_fields = {}
        for field in CHARFIELDS:
            acteur_fields[field] = [faker.word()]
            revisionacteur_fields[field] = [None]
        for field_list in [acteur_fields, revisionacteur_fields]:
            field_list["id"] = ["a1"]
            field_list["statut"] = [constants.ACTEUR_ACTIF]
            field_list["parent_id"] = [None]
            field_list["source_id"] = [1]
        df_acteur = pd.DataFrame(acteur_fields)
        df_revisionacteur = pd.DataFrame(revisionacteur_fields)
        df_result = compute_acteur(df_acteur, df_revisionacteur)["df_acteur_merged"]
        df_result.drop(columns=["uuid"], inplace=True)
        # Trier les colonnes avant de comparer
        df_result = df_result.sort_index(axis=1)
        df_acteur = df_acteur.sort_index(axis=1)
        pd.testing.assert_frame_equal(df_result, df_acteur)

    def test_set_value(self):
        acteur_fields = {}
        revisionacteur_fields = {}
        for field in CHARFIELDS:
            acteur_fields[field] = [faker.word()]
            revisionacteur_fields[field] = [faker.word()]
        for field_list in [acteur_fields, revisionacteur_fields]:
            field_list["id"] = ["a1"]
            field_list["statut"] = [constants.ACTEUR_ACTIF]
            field_list["parent_id"] = [None]
            field_list["source_id"] = [1]
        df_acteur = pd.DataFrame(acteur_fields)
        df_revisionacteur = pd.DataFrame(revisionacteur_fields)
        df_result = compute_acteur(df_acteur, df_revisionacteur)["df_acteur_merged"]
        df_result.drop(columns=["uuid"], inplace=True)
        # Trier les colonnes avant de comparer
        df_result = df_result.sort_index(axis=1)
        df_revisionacteur = df_revisionacteur.sort_index(axis=1)
        pd.testing.assert_frame_equal(df_result, df_revisionacteur)
