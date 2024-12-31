from unittest.mock import patch

import pandas as pd
import pytest
from sources.config.airflow_params import TRANSFORMATION_MAPPING
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.business_logic.source_data_normalize import (
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

    # def test_geopoint_to_longitude_latitude(
    #     self, df_sinoe, product_mapping, dechet_mapping, acteurtype_id_by_code
    # ):
    #     df = df_normalize_sinoe(
    #         df=df_sinoe,
    #         product_mapping=product_mapping,
    #         dechet_mapping=dechet_mapping,
    #     )
    #     assert df.iloc[0]["longitude"] == 3.120109493179493
    #     assert df.iloc[0]["latitude"] == 48.4812237361283
    #     assert "_geopoint" not in df.columns


class TestSourceDataNormalize:
    # FIXME : Add tests to check all kind of transformation is applied
    def test_normalization_rules_is_called(self):
        dag_config_kwargs = {
            "normalization_rules": [
                {
                    "origin": "nom origin",
                    "transformation": "test_fct",
                    "destination": "nom destination",
                },
                {
                    "origin": "nom",
                    "transformation": "test_fct",
                    "destination": "nom",
                },
                {"keep": "identifiant_unique"},
            ],
            "product_mapping": {},
            "endpoint": "http://example.com/api",
        }
        TRANSFORMATION_MAPPING["test_fct"] = lambda x, y: "success"
        df = source_data_normalize(
            df_acteur_from_source=pd.DataFrame(
                {
                    "identifiant_unique": ["id"],
                    "nom origin": ["nom origin 1"],
                    "nom": ["nom"],
                }
            ),
            dag_config=DAGConfig.model_validate(dag_config_kwargs),
            dag_id="dag_id",
        )
        assert "nom destination" in df.columns
        assert df["nom destination"].iloc[0] == "success"

        assert "nom" in df.columns
        assert df["nom"].iloc[0] == "success"

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


class TestRemoveUndesired_lines:
    # FIXME : Add tests
    pass

    # # "service_a_domicile"
    # def test_service_a_domicile(
    #     self,
    #     df_empty_acteurs_from_db,
    # ):

    #     result = propose_acteur_changes(
    #         df=pd.DataFrame(
    #             {
    #                 "identifiant_unique": ["1", "2"],
    #                 "service_a_domicile": ["Oui exclusivement", "Non"],
    #             }
    #         ),
    #         df_acteurs=df_empty_acteurs_from_db,
    #     )
    #     result_df = result["df"]

    #     assert len(result_df) == 1
    #     assert result_df["service_a_domicile"].iloc[0] == "Non"
    #     assert result_df["identifiant_unique"].iloc[0] == "2"
