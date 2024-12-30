from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sources.config.airflow_params import TRANSFORMATION_MAPPING
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

    @pytest.mark.parametrize("produitsdechets_acceptes", (None, "NP|01.22"))
    def test_produitsdechets_acceptes_exclude_entries_not_mapped(
        self,
        product_mapping,
        dechet_mapping,
        acteurtype_id_by_code,
        produitsdechets_acceptes,
    ):
        df_normalised = pd.DataFrame(
            {
                "identifiant_externe": ["DECHET_2"],
                "ANNEE": [2024],
                "_geopoint": ["48.4812237361283,3.120109493179493"],
                "produitsdechets_acceptes": [produitsdechets_acceptes],
                "public_accueilli": ["DMA"],
            },
        )

        df = df_normalize_sinoe(
            df=df_normalised,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
        assert len(df) == 0

    @pytest.mark.parametrize(
        "produitsdechets_acceptes, produitsdechets_acceptes_expected",
        (
            [
                "01.1|07.25|07.6",
                ["Solvants usés", "Papiers cartons mêlés triés", "Déchets textiles"],
            ],
            ["07.6", ["Déchets textiles"]],
        ),
    )
    def test_produitsdechets_acceptes_convert_dechet_codes_to_our_codes(
        self,
        product_mapping,
        dechet_mapping,
        acteurtype_id_by_code,
        produitsdechets_acceptes,
        produitsdechets_acceptes_expected,
    ):
        df_normalised = pd.DataFrame(
            {
                "identifiant_externe": ["DECHET_2"],
                "ANNEE": [2024],
                "_geopoint": ["48.4812237361283,3.120109493179493"],
                "produitsdechets_acceptes": [produitsdechets_acceptes],
                "public_accueilli": ["DMA"],
            },
        )
        df = df_normalize_sinoe(
            df=df_normalised,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
        assert (
            df.iloc[0]["produitsdechets_acceptes"] == produitsdechets_acceptes_expected
        )

    @pytest.mark.parametrize(
        "public_accueilli, public_accueilli_expected",
        [
            ("DMA", "Particuliers"),
            ("DMA/PRO", "Particuliers et professionnels"),
            ("PRO", "Professionnels"),
        ],
    )
    def test_public_accueilli_particuliers(
        self,
        product_mapping,
        dechet_mapping,
        acteurtype_id_by_code,
        public_accueilli,
        public_accueilli_expected,
    ):
        df_normalised = pd.DataFrame(
            {
                "identifiant_externe": ["DECHET_2"],
                "ANNEE": [2024],
                "_geopoint": ["48.4812237361283,3.120109493179493"],
                "produitsdechets_acceptes": ["01.1|07.25|07.6"],
                "public_accueilli": [public_accueilli],
            },
        )
        df = df_normalize_sinoe(
            df=df_normalised,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
        assert df.iloc[0]["public_accueilli"] == public_accueilli_expected

    def test_point_de_collecte_ou_de_reprise_des_dechets(
        self, product_mapping, dechet_mapping, acteurtype_id_by_code, df_sinoe
    ):
        df = df_normalize_sinoe(
            df=df_sinoe,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
        assert df.iloc[0]["point_de_collecte_ou_de_reprise_des_dechets"]

    def test_acteur_type_id(
        self, df_sinoe, product_mapping, dechet_mapping, acteurtype_id_by_code
    ):
        df = df_normalize_sinoe(
            df=df_sinoe,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
        assert df.iloc[0]["acteur_type_id"] == 2

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
                acteurtype_id_by_code=acteurtype_id_by_code,
            )

    def test_drop_annee_column(
        self, df_sinoe, product_mapping, dechet_mapping, acteurtype_id_by_code
    ):
        df = df_normalize_sinoe(
            df=df_sinoe,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
        assert "ANNEE" not in df.columns

    def test_geopoint_to_longitude_latitude(
        self, df_sinoe, product_mapping, dechet_mapping, acteurtype_id_by_code
    ):
        df = df_normalize_sinoe(
            df=df_sinoe,
            product_mapping=product_mapping,
            dechet_mapping=dechet_mapping,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )
        assert df.iloc[0]["longitude"] == 3.120109493179493
        assert df.iloc[0]["latitude"] == 48.4812237361283
        assert "_geopoint" not in df.columns


class TestSourceDataNormalize:
    """
    Test de la fonction source_data_normalize
    - [ ] test que la fonction source_data_normalize appelle df_normalize_sinoe
    - [ ] test renommage des colonnes
    - [ ] test source_id et source_code
    - [ ] test identifiant_unique
    - [ ] test combine_columns_categories
    - [ ] test merge_duplicated_acteurs
    - [ ] test columns_to_add_by_default
    - [ ] test adresse_format_ban
    - [x] test statut
    - [x] test public_accueilli (+ suppression des pro)
    - [x] test uniquement_sur_rdv
    - [x] test exclusivite_de_reprisereparation
    - [x] test reprise
    - [x] test labels_etou_bonus
    - [ ] test url
    - [ ] test acteur_type_id
    - [ ] test Suppresion des colonnes non voulues
    - [ ] test ignore_duplicates
    - [ ] test produitsdechets_acceptes vide ou None
    - [x] test transformation from column_transformations is called
    """

    @pytest.fixture
    def source_data_normalize_kwargs(self, acteurtype_id_by_code, source_id_by_code):
        return {
            "df_acteur_from_source": pd.DataFrame(),
            "source_code": None,
            "column_mapping": {},
            "column_transformations": [],
            "columns_to_add_by_default": {},
            "label_bonus_reparation": "bonus_reparation",
            "validate_address_with_ban": False,
            "ignore_duplicates": False,
            "combine_columns_categories": [],
            "merge_duplicated_acteurs": False,
            "product_mapping": {},
            "dechet_mapping": {},
            "acteurtype_id_by_code": acteurtype_id_by_code,
            "source_id_by_code": source_id_by_code,
        }

    @pytest.mark.parametrize(
        "statut, statut_expected",
        [
            (None, "ACTIF"),
            ("fake", "ACTIF"),
            (np.nan, "ACTIF"),
            (0, "SUPPRIME"),
            (1, "ACTIF"),
            ("ACTIF", "ACTIF"),
            ("INACTIF", "INACTIF"),
            ("SUPPRIME", "SUPPRIME"),
        ],
    )
    def test_statut(self, statut, statut_expected, source_data_normalize_kwargs):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
                "statut": [statut],
            }
        )
        df = source_data_normalize(**source_data_normalize_kwargs)

        assert df["statut"].iloc[0] == statut_expected

    def test_statut_no_column(self, source_data_normalize_kwargs):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
            }
        )
        df = source_data_normalize(**source_data_normalize_kwargs)

        assert df["statut"].iloc[0] == "ACTIF"

    @pytest.mark.parametrize(
        "label_et_bonus, label_et_bonus_expected",
        [
            ("label_et_bonus", "label_et_bonus"),
            ("label_et_bonus1|label_et_bonus2", "label_et_bonus1|label_et_bonus2"),
            (
                "Agréé Bonus Réparation|label_et_bonus2",
                "bonus_reparation|label_et_bonus2",
            ),
        ],
    )
    def test_label_bonus(
        self, label_et_bonus, label_et_bonus_expected, source_data_normalize_kwargs
    ):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "acteur_type_id": ["decheterie"],
                "labels_etou_bonus": [label_et_bonus],
                "produitsdechets_acceptes": ["Plastic Box"],
            }
        )
        df = source_data_normalize(**source_data_normalize_kwargs)

        assert df["labels_etou_bonus"].iloc[0] == label_et_bonus_expected

    @pytest.mark.parametrize(
        "public_accueilli, expected_public_accueilli",
        [
            (None, None),
            ("fake", None),
            ("PARTICULIERS", "Particuliers"),
            ("Particuliers", "Particuliers"),
            ("Particuliers et professionnels", "Particuliers et professionnels"),
        ],
    )
    def test_public_accueilli(
        self,
        public_accueilli,
        expected_public_accueilli,
        source_data_normalize_kwargs,
    ):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "public_accueilli": [public_accueilli],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
            }
        )
        df = source_data_normalize(**source_data_normalize_kwargs)

        assert df["public_accueilli"][0] == expected_public_accueilli

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
        source_data_normalize_kwargs,
    ):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "public_accueilli": [public_accueilli],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
            }
        )
        with pytest.raises(ValueError):
            source_data_normalize(**source_data_normalize_kwargs)

    @pytest.mark.parametrize(
        "uniquement_sur_rdv,expected_uniquement_sur_rdv",
        [
            (None, False),
            (False, False),
            (True, True),
            ("oui", True),
            ("Oui", True),
            (" Oui ", True),
            ("non", False),
            ("NON", False),
            (" NON ", False),
            ("", False),
            (" ", False),
            ("fake", False),
        ],
    )
    def test_uniquement_sur_rdv(
        self,
        uniquement_sur_rdv,
        expected_uniquement_sur_rdv,
        source_data_normalize_kwargs,
    ):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "uniquement_sur_rdv": [uniquement_sur_rdv],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
            }
        )
        df = source_data_normalize(**source_data_normalize_kwargs)

        assert df["uniquement_sur_rdv"][0] == expected_uniquement_sur_rdv

    @pytest.mark.parametrize(
        "reprise,expected_reprise",
        [
            (None, None),
            ("1 pour 0", "1 pour 0"),
            ("1 pour 1", "1 pour 1"),
            ("non", "1 pour 0"),
            ("oui", "1 pour 1"),
            ("fake", None),
        ],
    )
    def test_reprise(
        self,
        reprise,
        expected_reprise,
        source_data_normalize_kwargs,
    ):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "reprise": [reprise],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
            }
        )
        df = source_data_normalize(**source_data_normalize_kwargs)
        assert df["reprise"][0] == expected_reprise

    @pytest.mark.parametrize(
        "exclusivite_de_reprisereparation, expected_exclusivite_de_reprisereparation",
        [
            (None, False),
            (False, False),
            (True, True),
            ("oui", True),
            ("Oui", True),
            (" Oui ", True),
            ("non", False),
            ("NON", False),
            (" NON ", False),
            ("", False),
            (" ", False),
            ("fake", False),
        ],
    )
    def test_exclusivite_de_reprisereparation(
        self,
        exclusivite_de_reprisereparation,
        expected_exclusivite_de_reprisereparation,
        source_data_normalize_kwargs,
    ):
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "exclusivite_de_reprisereparation": [exclusivite_de_reprisereparation],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
            }
        )
        df = source_data_normalize(**source_data_normalize_kwargs)
        assert (
            df["exclusivite_de_reprisereparation"][0]
            == expected_exclusivite_de_reprisereparation
        )

    def test_column_transformations_is_called(self, source_data_normalize_kwargs):

        source_data_normalize_kwargs["column_transformations"] = [
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
        ]
        source_data_normalize_kwargs["df_acteur_from_source"] = pd.DataFrame(
            {
                "identifiant_externe": ["1"],
                "ecoorganisme": ["source1"],
                "source_id": ["source_id1"],
                "acteur_type_id": ["decheterie"],
                "produitsdechets_acceptes": ["Plastic Box"],
                "nom origin": ["nom origin 1"],
                "nom": ["nom"],
            }
        )

        TRANSFORMATION_MAPPING["test_fct"] = lambda x: "success"
        df = source_data_normalize(**source_data_normalize_kwargs)
        assert "nom destination" in df.columns
        assert df["nom destination"].iloc[0] == "success"

        assert "nom" in df.columns
        assert df["nom"].iloc[0] == "success"


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
