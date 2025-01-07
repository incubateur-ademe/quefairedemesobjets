from unittest.mock import patch

import pandas as pd
import pytest
from sources.config.airflow_params import TRANSFORMATION_MAPPING
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.source_data_normalize import (
    _remove_undesired_lines,
    df_normalize_pharmacie,
    df_normalize_sinoe,
    source_data_normalize,
)

"""
TODO:
Pour la fonction df_nomalize_sinoe

"""


@pytest.fixture
def df_sinoe():
    return pd.DataFrame(
        {
            "identifiant_externe": ["DECHET_1"],
            "ANNEE": [2024],
            "_geopoint": ["48.4812237361283,3.120109493179493"],
            "produitsdechets_acceptes": ["07.6"],
            "public_accueilli": ["DMA"],
        },
    )


@pytest.fixture
def product_mapping():
    return {
        "Solvants usés": "Produits chimiques - Solvants",
        "Papiers cartons mêlés triés": [
            "papiers_graphiques",
            "emballage_carton",
        ],
        "Déchets textiles": ["vêtement", "linge de maison"],
    }


@pytest.fixture
def dechet_mapping():
    return {
        "01.1": "Solvants usés",
        "07.25": "Papiers cartons mêlés triés",
        "07.6": "Déchets textiles",
        "01.22": "Déchets alcalins",
        "NP": "Non précisé",
    }


class TestSourceDataNormalizeSinoe:
    """
    Test de la fonction df_normalize_sinoe
    """

    def test_annee_unique(self, product_mapping, dechet_mapping, acteurtype_id_by_code):
        df = pd.DataFrame(
            {
                "identifiant_externe": ["DECHET_1", "DECHET_2"],
                "ANNEE": [2024, 2025],
                "_geopoint": [
                    "48.4812237361283,3.120109493179493",
                    "48.4812237361283,3.120109493179493",
                ],
                "produitsdechets_acceptes": ["07.6", "07.6"],
                "public_accueilli": ["DMA", "DMA"],
            },
        )

        with pytest.raises(ValueError):
            df = df_normalize_sinoe(
                df=df,
                product_mapping=product_mapping,
                dechet_mapping=dechet_mapping,
            )

    def test_drop_annee_column(
        self, df_sinoe, product_mapping, dechet_mapping, acteurtype_id_by_code
    ):
        df = df_normalize_sinoe(
            df=df_sinoe,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
        )
        assert "ANNEE" not in df.columns


NORMALIZATION_RULES = [
    {
        "origin": "col_to_rename",
        "destination": "col_renamed",
    },
    {
        "origin": "nom origin",
        "transformation": "test_fct",
        "destination": "nom destination",
    },
    {"column": "string_col", "value": "value of col"},
    {"column": "list_col", "value": ["col1", "col2"]},
    {
        "origin": ["nom"],
        "transformation": "test_fct",
        "destination": ["nom"],
    },
    {"keep": "identifiant_unique"},
    {"remove": "col_to_remove"},
]


class TestSourceDataNormalize:

    def test_source_data_normalize_normalization_rules_are_called(self):
        dag_config_kwargs = {
            "normalization_rules": NORMALIZATION_RULES,
            "product_mapping": {},
            "endpoint": "http://example.com/api",
        }
        TRANSFORMATION_MAPPING["test_fct"] = lambda x, y: "success"
        df = source_data_normalize(
            df_acteur_from_source=pd.DataFrame(
                {
                    "identifiant_unique": ["id"],
                    "col_to_remove": ["fake remove"],
                    "col_to_rename": ["fake rename"],
                    "nom origin": ["nom origin 1"],
                    "nom": ["nom"],
                }
            ),
            dag_config=DAGConfig.model_validate(dag_config_kwargs),
            dag_id="dag_id",
        )

        assert "col_to_rename" not in df.columns
        assert "col_renamed" in df.columns
        assert df["col_renamed"].iloc[0] == "fake rename"

        assert "nom destination" in df.columns
        assert df["nom destination"].iloc[0] == "success"

        assert "string_col" in df.columns
        assert df["string_col"].iloc[0] == "value of col"

        assert "list_col" in df.columns
        assert df["list_col"].iloc[0] == ["col1", "col2"]

        assert "nom" in df.columns
        assert df["nom"].iloc[0] == "success"

        assert "identifiant_unique" in df.columns
        assert df["identifiant_unique"].iloc[0] == "id"

        assert "col_to_remove" not in df.columns

    def test_source_data_normalize_unhandles_column_raise(self):
        dag_config_kwargs = {
            "normalization_rules": NORMALIZATION_RULES,
            "product_mapping": {},
            "endpoint": "http://example.com/api",
        }

        with pytest.raises(ValueError) as erreur:
            source_data_normalize(
                df_acteur_from_source=pd.DataFrame(
                    {
                        "identifiant_unique": ["id"],
                        "col_to_remove": ["fake remove"],
                        "col_to_rename": ["fake rename"],
                        "nom origin": ["nom origin 1"],
                        "nom": ["nom"],
                        "col_make_it_raise": ["fake"],
                    }
                ),
                dag_config=DAGConfig.model_validate(dag_config_kwargs),
                dag_id="dag_id",
            )
        assert "Le dataframe n'a pas les colonnes attendues" in str(erreur.value)
        assert "col_make_it_raise" in str(erreur.value)

    # @pytest.mark.parametrize(
    #     "statut, statut_expected",
    #     [
    #         (None, "ACTIF"),
    #         ("fake", "ACTIF"),
    #         (np.nan, "ACTIF"),
    #         (0, "SUPPRIME"),
    #         (1, "ACTIF"),
    #         ("ACTIF", "ACTIF"),
    #         ("INACTIF", "INACTIF"),
    #         ("SUPPRIME", "SUPPRIME"),
    #     ],
    # )
    # def test_statut(self, statut, statut_expected, source_data_normalize_kwargs):
    #     source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
    #         {
    #             "identifiant_externe": ["1"],
    #             "ecoorganisme": ["source1"],
    #             "source_id": ["source_id1"],
    #             "acteur_type_id": ["decheterie"],
    #             "produitsdechets_acceptes": ["Plastic Box"],
    #             "statut": [statut],
    #         }
    #     )
    #     df = source_data_normalize(**source_data_normalize_kwargs)

    #     assert df["statut"].iloc[0] == statut_expected

    @pytest.mark.parametrize(
        "public_accueilli",
        [
            "PROFESSIONNELS",
            "Professionnels",
        ],
    )
    def test_public_accueilli_filtre_pro(
        self,
        public_accueilli,
        dag_config,
    ):
        with pytest.raises(ValueError):
            source_data_normalize(
                dag_config=dag_config,
                df_acteur_from_source=pd.DataFrame({"identifiant_externe": ["1"]}),
                dag_id="id",
            )


class TestDfNormalizePharmacie:
    """
    Test de la fonction df_normalize_pharmacie
    """

    @patch(
        "sources.tasks.business_logic.source_data_normalize.enrich_from_ban_api",
        autospec=True,
    )
    def test_df_normalize_pharmacie(self, mock_enrich_from_ban_api):
        def _enrich_from_ban_api(row):
            if row["ville"] == "Paris":
                row["latitude"] = 48.8566
                row["longitude"] = 2.3522
            else:
                row["latitude"] = 0
                row["longitude"] = 0
            return row

        mock_enrich_from_ban_api.side_effect = _enrich_from_ban_api

        df = pd.DataFrame(
            {
                "adresse": ["123 Rue de Paris", "456 Avenue de Lyon"],
                "code_postal": ["75001", "69000"],
                "ville": ["Paris", "Lyon"],
            }
        )

        # Appeler la fonction df_normalize_pharmacie
        result_df = df_normalize_pharmacie(df)

        assert mock_enrich_from_ban_api.call_count == len(df)
        pd.testing.assert_frame_equal(
            result_df,
            pd.DataFrame(
                {
                    "adresse": ["123 Rue de Paris"],
                    "code_postal": ["75001"],
                    "ville": ["Paris"],
                    "latitude": [48.8566],
                    "longitude": [2.3522],
                }
            ),
        )


class TestRemoveUndesiredLines:
    @pytest.mark.parametrize(
        "df, expected_df",
        [
            # Cas suppression service à domicile
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2", "id3"],
                        "service_a_domicile": [
                            "non",
                            "oui exclusivement",
                            "service à domicile uniquement",
                        ],
                        "public_accueilli": [
                            "Particuliers",
                            "Particuliers",
                            "Particuliers",
                        ],
                        "souscategorie_codes": [["code1"], ["code2"], ["code3"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1"],
                        "service_a_domicile": ["non"],
                        "public_accueilli": ["Particuliers"],
                        "souscategorie_codes": [["code1"]],
                    }
                ),
            ),
            # Cas suppression professionnele
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2", "id3", "id4"],
                        "service_a_domicile": ["non", "non", "non", "oui"],
                        "public_accueilli": [
                            "Particuliers",
                            "Particuliers et professionnels",
                            "Professionnels",
                            "Aucun",
                        ],
                        "souscategorie_codes": [
                            ["code1"],
                            ["code2"],
                            ["code3"],
                            ["code4"],
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2", "id4"],
                        "service_a_domicile": ["non", "non", "oui"],
                        "public_accueilli": [
                            "Particuliers",
                            "Particuliers et professionnels",
                            "Aucun",
                        ],
                        "souscategorie_codes": [["code1"], ["code2"], ["code4"]],
                    }
                ),
            ),
            # Cas avec suppression des lignes sans produits acceptés
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2", "id3"],
                        "service_a_domicile": ["non", "non", "non"],
                        "public_accueilli": [
                            "Particuliers",
                            "Particuliers",
                            "Particuliers",
                        ],
                        "souscategorie_codes": [["code1"], [], ["code3"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id3"],
                        "service_a_domicile": ["non", "non"],
                        "public_accueilli": ["Particuliers", "Particuliers"],
                        "souscategorie_codes": [["code1"], ["code3"]],
                    }
                ),
            ),
        ],
    )
    def test_remove_undesired_lines_suppressions(self, df, expected_df, dag_config):
        # Mock the DAGConfig

        result_df = _remove_undesired_lines(df, dag_config)
        pd.testing.assert_frame_equal(
            result_df.reset_index(drop=True), expected_df.reset_index(drop=True)
        )

    def test_merge_duplicated_acteurs(self, dag_config):
        dag_config.merge_duplicated_acteurs = True
        result = _remove_undesired_lines(
            pd.DataFrame(
                {
                    "identifiant_unique": ["id1", "id1", "id2"],
                    "service_a_domicile": ["non", "non", "non"],
                    "public_accueilli": [
                        "Particuliers",
                        "Particuliers",
                        "Particuliers",
                    ],
                    "souscategorie_codes": [["code1"], ["code2"], ["code3"]],
                }
            ),
            dag_config,
        )
        result = result.sort_values("identifiant_unique")
        result = result.reset_index(drop=True)

        expected_df = pd.DataFrame(
            {
                "identifiant_unique": ["id1", "id2"],
                "service_a_domicile": ["non", "non"],
                "public_accueilli": ["Particuliers", "Particuliers"],
                "souscategorie_codes": [["code1", "code2"], ["code3"]],
            }
        )
        expected_df.reset_index(drop=True)

        pd.testing.assert_frame_equal(result, expected_df)

    def test_ignore_duplicates(self, dag_config):
        dag_config.ignore_duplicates = True
        result = _remove_undesired_lines(
            pd.DataFrame(
                {
                    "identifiant_unique": ["id1", "id1", "id2"],
                    "service_a_domicile": ["non", "non", "non"],
                    "public_accueilli": [
                        "Particuliers",
                        "Particuliers",
                        "Particuliers",
                    ],
                    "souscategorie_codes": [["code1"], ["code2"], ["code3"]],
                }
            ),
            dag_config,
        )
        result = result.sort_values("identifiant_unique")
        result = result.reset_index(drop=True)

        expected_df = pd.DataFrame(
            {
                "identifiant_unique": ["id1", "id2"],
                "service_a_domicile": ["non", "non"],
                "public_accueilli": ["Particuliers", "Particuliers"],
                "souscategorie_codes": [["code1"], ["code3"]],
            }
        )
        expected_df.reset_index(drop=True)

        pd.testing.assert_frame_equal(result, expected_df)
