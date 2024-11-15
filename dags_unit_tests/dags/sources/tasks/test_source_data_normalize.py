import pandas as pd
import pytest
from sources.tasks.source_data_normalize import df_normalize_sinoe

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


@pytest.fixture
def acteurtype_id_by_code():
    return {
        "commerce": 1,
        "decheterie": 2,
        "autre": 3,
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
    - [ ] test statut
    - [ ] test public_accueilli (+ suppression des pro)
    - [ ] test uniquement_sur_rdv
    - [ ] test exclusivite_de_reprisereparation
    - [ ] test reprise
    - [ ] test labels_etou_bonus
    - [ ] test url
    - [ ] test acteur_type_id
    - [ ] test Suppresion des colonnes non voulues
    - [ ] test ignore_duplicates
    - [ ] test produitsdechets_acceptes vide ou None
    """

    pass
