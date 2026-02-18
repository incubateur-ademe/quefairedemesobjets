from unittest.mock import patch

import pandas as pd
import pytest
from sources.config.airflow_params import TRANSFORMATION_MAPPING
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.source_data_normalize import (
    _remove_undesired_lines,
    _transform_columns,
    df_normalize_pharmacie,
    df_normalize_sinoe,
    source_data_normalize,
)
from sources.tasks.transform.exceptions import ImportSourceValueWarning

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
            )

    def test_drop_annee_column(
        self, df_sinoe, product_mapping, dechet_mapping, acteurtype_id_by_code
    ):
        df = df_normalize_sinoe(
            df=df_sinoe,
        )
        assert "ANNEE" not in df.columns


NORMALIZATION_RULES = [
    {
        "origin": "col_to_rename",
        "destination": "col_renamed",
    },
    {
        "origin": "nom origin",
        "transformation": "test_fct_transform_column",
        "destination": "nom destination",
    },
    {"column": "string_col", "value": "value of col"},
    {"column": "list_col", "value": ["col1", "col2"]},
    {
        "origin": ["nom"],
        "transformation": "test_fct_transform_df",
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
        TRANSFORMATION_MAPPING["test_fct_transform_column"] = lambda x, y: "success"
        TRANSFORMATION_MAPPING["test_fct_transform_df"] = lambda x, y: pd.Series(
            {"nom": "success"}
        )
        df, _, _, _ = source_data_normalize(
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

    def test_transform_columns_returns_empty_string_on_warning(self):
        """
        Test  that if an ImportSourceValueWarning is raised,
        the value in the DataFrame is an empty string
        """
        normalization_rules = [
            {
                "origin": "col_origin",
                "transformation": "test_fct_raise_warning",
                "destination": "col_destination",
            },
            {"keep": "identifiant_unique"},
        ]
        dag_config_kwargs = {
            "normalization_rules": normalization_rules,
            "product_mapping": {},
            "endpoint": "http://example.com/api",
        }

        class ImportSourceValueWarningTest(ImportSourceValueWarning):
            pass

        # Fonction de transformation qui lève une ImportSourceValueWarning
        def raise_warning(value, dag_config):
            raise ImportSourceValueWarningTest("Test warning")

        TRANSFORMATION_MAPPING["test_fct_raise_warning"] = raise_warning

        df = pd.DataFrame(
            {
                "identifiant_unique": ["id1", "id2"],
                "col_origin": ["value1", "value2"],
            }
        )
        # Initialiser log_warning comme dans source_data_normalize
        df["log_warning"] = [[] for _ in range(len(df))]

        result_df = _transform_columns(df, DAGConfig.model_validate(dag_config_kwargs))

        # Vérifier que la colonne de destination existe
        assert "col_destination" in result_df.columns
        # Vérifier que toutes les valeurs sont des chaînes vides car l'erreur est levée
        assert result_df["col_destination"].iloc[0] == ""
        assert result_df["col_destination"].iloc[1] == ""
        # Vérifier que les warnings ont été ajoutés
        assert len(result_df["log_warning"].iloc[0]) == 1
        assert len(result_df["log_warning"].iloc[1]) == 1

    def test_source_data_normalize_normalization_remove_unknown_columns(self):
        normalization_rules = [
            {"keep": "identifiant_unique"},
            {"remove": "col_to_remove"},
            {"remove": "unknown_column"},
        ]
        dag_config_kwargs = {
            "normalization_rules": normalization_rules,
            "product_mapping": {},
            "endpoint": "http://example.com/api",
        }
        TRANSFORMATION_MAPPING["test_fct_transform_column"] = lambda x, y: "success"
        TRANSFORMATION_MAPPING["test_fct_transform_df"] = lambda x, y: pd.Series(
            {"nom": "success"}
        )
        df, _, _, _ = source_data_normalize(
            df_acteur_from_source=pd.DataFrame(
                {
                    "identifiant_unique": ["id"],
                    "col_to_remove": ["fake remove"],
                }
            ),
            dag_config=DAGConfig.model_validate(dag_config_kwargs),
            dag_id="dag_id",
        )
        assert "identifiant_unique" in df.columns
        assert "col_to_remove" not in df.columns
        assert "unknown_column" not in df.columns

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
        assert (
            "Le dataframe normalisé (données sources) n'a pas les colonnes attendues"
            in str(erreur.value)
        )
        assert "col_make_it_raise" in str(erreur.value)

    # TODO : ajout des valeurs avec parametrize
    @pytest.mark.parametrize(
        "null_value",
        [
            "Null",
            "null",
            "NULL",
            "None",
            "none",
            "NONE",
            "nan",
            "NAN",
            "NaN",
            "na",
            "n/a",
            "non applicable",
            "NON APPLICABLE",
            "-",
            "aucun",
            "Aucun",
        ],
    )
    def test_remove_explicit_null(self, null_value):
        dag_config = DAGConfig.model_validate(
            {
                "normalization_rules": [
                    {"keep": "identifiant_unique"},
                    {"keep": "nom"},
                    {"keep": "liste"},
                ],
                "endpoint": "https://example.com/api",
                "product_mapping": {"product1": "code1"},
            }
        )
        df, _, _, _ = source_data_normalize(
            dag_config=dag_config,
            df_acteur_from_source=pd.DataFrame(
                {
                    "identifiant_unique": ["1", "2"],
                    "nom": ["fake nom", null_value],
                    "liste": [["fake nom"], ["fake nom", null_value]],
                }
            ),
            dag_id="id",
        )
        pd.testing.assert_frame_equal(
            df.reset_index(drop=True),
            pd.DataFrame(
                {
                    "identifiant_unique": ["1", "2"],
                    "nom": ["fake nom", ""],
                    "liste": [["fake nom"], ["fake nom"]],
                }
            ).reset_index(drop=True),
        )


class TestDfApplyOCA:
    """
    Test de la fonction df_normalize_oca
    """

    @pytest.fixture
    def dag_config_kwargs(self):
        return {
            "normalization_rules": [
                {"keep": "identifiant_unique"},
                {"keep": "nom"},
                {"keep": "source_code"},
                {"keep": "identifiant_externe"},
            ],
            "product_mapping": {},
            "endpoint": "https://example.com/api",
        }

    @pytest.fixture
    def df_acteur(self):
        return pd.DataFrame(
            {
                "identifiant_unique": ["id1", "id2"],
                "source_code": ["oca_1|oca_2", "oca_2"],
                "identifiant_externe": ["ext1", "ext2"],
                "nom": ["nom1", "nom2"],
            }
        )

    def test_apply_oca_config(self, dag_config_kwargs, df_acteur):
        dag_config_kwargs["oca"] = {"prefix": "ocatest", "deduplication_source": True}

        df, _, _, _ = source_data_normalize(
            df_acteur_from_source=df_acteur,
            dag_config=DAGConfig.model_validate(dag_config_kwargs),
            dag_id="dag_id",
        )

        expected_df = pd.DataFrame(
            {
                "identifiant_unique": [
                    "ocatest_oca_1_ext1",
                    "ocatest_oca_2_ext1",
                    "ocatest_oca_2_ext2",
                ],
                "source_code": ["ocatest_oca_1", "ocatest_oca_2", "ocatest_oca_2"],
                "identifiant_externe": ["ext1", "ext1", "ext2"],
                "nom": ["nom1", "nom1", "nom2"],
            }
        )

        pd.testing.assert_frame_equal(
            df.reset_index(drop=True), expected_df.reset_index(drop=True)
        )

    def test_apply_oca_config_no_deduplication_source(
        self, dag_config_kwargs, df_acteur
    ):
        dag_config_kwargs["oca"] = {"prefix": "ocatest"}

        df, _, _, _ = source_data_normalize(
            df_acteur_from_source=df_acteur,
            dag_config=DAGConfig.model_validate(dag_config_kwargs),
            dag_id="dag_id",
        )

        expected_df = pd.DataFrame(
            {
                "identifiant_unique": [
                    "ocatest_oca_1|oca_2_ext1",
                    "ocatest_oca_2_ext2",
                ],
                "source_code": ["ocatest_oca_1|oca_2", "ocatest_oca_2"],
                "identifiant_externe": ["ext1", "ext2"],
                "nom": ["nom1", "nom2"],
            }
        )

        pd.testing.assert_frame_equal(
            df.reset_index(drop=True), expected_df.reset_index(drop=True)
        )

    def test_apply_oca_config_no_prefix(self, dag_config_kwargs, df_acteur):
        dag_config_kwargs["oca"] = {"deduplication_source": True}

        df, _, _, _ = source_data_normalize(
            df_acteur_from_source=df_acteur,
            dag_config=DAGConfig.model_validate(dag_config_kwargs),
            dag_id="dag_id",
        )

        expected_df = pd.DataFrame(
            {
                "identifiant_unique": [
                    "oca_1_ext1",
                    "oca_2_ext1",
                    "oca_2_ext2",
                ],
                "source_code": ["oca_1", "oca_2", "oca_2"],
                "identifiant_externe": ["ext1", "ext1", "ext2"],
                "nom": ["nom1", "nom1", "nom2"],
            }
        )

        pd.testing.assert_frame_equal(
            df.reset_index(drop=True), expected_df.reset_index(drop=True)
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
                        "sous_categorie_codes": [["code1"], ["code2"], ["code3"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1"],
                        "service_a_domicile": ["non"],
                        "public_accueilli": ["Particuliers"],
                        "sous_categorie_codes": [["code1"]],
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
                        "sous_categorie_codes": [["code1"], [], ["code3"]],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id3"],
                        "service_a_domicile": ["non", "non"],
                        "public_accueilli": ["Particuliers", "Particuliers"],
                        "sous_categorie_codes": [["code1"], ["code3"]],
                    }
                ),
            ),
        ],
    )
    def test_remove_undesired_lines_suppressions(self, df, expected_df, dag_config):
        # Mock the DAGConfig

        result_df, _ = _remove_undesired_lines(df, dag_config)
        pd.testing.assert_frame_equal(
            result_df.reset_index(drop=True), expected_df.reset_index(drop=True)
        )

    def test_merge_duplicated(self, dag_config):
        result, _ = _remove_undesired_lines(
            pd.DataFrame(
                {
                    "identifiant_unique": ["id1", "id1", "id2"],
                    "service_a_domicile": ["non", "non", "non"],
                    "public_accueilli": [
                        "Particuliers",
                        "Particuliers",
                        "Particuliers",
                    ],
                    "label_codes": [["label1"], ["label2"], ["label3"]],
                    "acteur_service_codes": [
                        ["acteurservice1"],
                        ["acteurservice2"],
                        ["acteurservice3"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["sscat1", "sscat3"],
                            },
                            {"action": "action2", "sous_categories": ["sscat1"]},
                        ],
                        [
                            {"action": "action2", "sous_categories": ["sscat2"]},
                            {"action": "action3", "sous_categories": ["sscat3"]},
                        ],
                        [{"action": "action3", "sous_categories": ["sscat3"]}],
                    ],
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
                "label_codes": [["label1", "label2"], ["label3"]],
                "acteur_service_codes": [
                    ["acteurservice1", "acteurservice2"],
                    ["acteurservice3"],
                ],
                "proposition_service_codes": [
                    [
                        {"action": "action1", "sous_categories": ["sscat1", "sscat3"]},
                        {"action": "action2", "sous_categories": ["sscat1", "sscat2"]},
                        {"action": "action3", "sous_categories": ["sscat3"]},
                    ],
                    [{"action": "action3", "sous_categories": ["sscat3"]}],
                ],
            }
        )
        expected_df.reset_index(drop=True)

        pd.testing.assert_frame_equal(result, expected_df)
