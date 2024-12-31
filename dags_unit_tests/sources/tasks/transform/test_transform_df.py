import pandas as pd
import pytest
from sources.tasks.transform.transform_df import (
    clean_action_codes,
    clean_identifiant_externe,
    clean_identifiant_unique,
    clean_label_codes,
    clean_siret_and_siren,
    clean_telephone,
    get_latlng_from_geopoint,
    merge_duplicates,
    merge_sous_categories_columns,
)


class TestMergeDuplicates:

    @pytest.mark.parametrize(
        "df, expected_df",
        [
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "souscategorie_codes": [
                            ["Plastic Box", "Metal", "Aàèë l'test"],
                            ["Plastic Box", "Metal", "Aàèë l'test"],
                        ],
                        "other_column": ["A", "B"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "souscategorie_codes": [
                            ["Aàèë l'test", "Metal", "Plastic Box"]
                        ],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "souscategorie_codes": [
                            ["Plastic", "Metal"],
                            ["Metal", "Glass"],
                            ["Paper"],
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "souscategorie_codes": [
                            ["Plastic", "Metal"],
                            ["Metal", "Glass"],
                            ["Paper"],
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 1],
                        "souscategorie_codes": [
                            ["Plastic", "Metal"],
                            ["Metal", "Glass"],
                            ["Paper"],
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "souscategorie_codes": [["Glass", "Metal", "Paper", "Plastic"]],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 2, 3, 3, 3],
                        "souscategorie_codes": [
                            ["Plastic", "Metal"],
                            ["Metal", "Glass"],
                            ["Paper"],
                            ["Glass", "Plastic"],
                            ["Plastic", "Metal"],
                            ["Metal"],
                        ],
                        "other_column": ["A", "B", "C", "D", "E", "F"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "souscategorie_codes": [
                            ["Glass", "Metal", "Plastic"],
                            ["Paper"],
                            ["Glass", "Metal", "Plastic"],
                        ],
                        "other_column": ["A", "C", "D"],
                    }
                ),
            ),
        ],
    )
    def test_merge_duplicates(self, df, expected_df):

        result_df = merge_duplicates(df)

        result_df = result_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )
        expected_df = expected_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )

        pd.testing.assert_frame_equal(result_df, expected_df)


class TestCleanTelephone:
    @pytest.mark.parametrize(
        "phone_number, code_postal, expected_phone_number",
        [
            (None, None, None),
            (pd.NA, None, None),
            ("1 23 45 67 89", "75001", "0123456789"),
            ("33 1 23 45 67 89", "75001", "0123456789"),
            ("0612345678", "75001", "0612345678"),
            ("+33612345678", "75001", "+33612345678"),
        ],
    )
    def test_clean_telephone(self, phone_number, code_postal, expected_phone_number):
        result = clean_telephone(
            pd.Series({"telephone": phone_number, "code_postal": code_postal}), None
        )
        assert result["telephone"] == expected_phone_number


class TestCleanSiretAndSiren:
    @pytest.mark.parametrize(
        "siret, siren, expected_siret, expected_siren",
        [
            (None, None, None, None),
            ("12345678901234", None, "12345678901234", "123456789"),
            (None, "123456789", None, "123456789"),
            ("98765432109876", "987654321", "98765432109876", "987654321"),
            ("12345678901234", "123456789", "12345678901234", "123456789"),
            ("12345678901234", "987654321", "12345678901234", "987654321"),
        ],
    )
    def test_clean_siret_and_siren(self, siret, siren, expected_siret, expected_siren):
        row = pd.Series({"siret": siret, "siren": siren})
        result = clean_siret_and_siren(row, None)
        assert result["siret"] == expected_siret
        assert result["siren"] == expected_siren


class TestCleanIdentifiantExterne:

    @pytest.mark.parametrize(
        "identifiant_externe, nom, expected_identifiant_externe",
        [
            (None, "nom", "nom"),
            (None, "nom-nom nom_nom__nom", "nomnom_nom_nom_nom"),
            ("12345", "nom", "12345"),
            (" 12345 ", "nom", "12345"),
            ("ABC123", "nom", "ABC123"),
            (" abc123 ", "nom", "abc123"),
        ],
    )
    def test_clean_identifiant_externe(
        self, identifiant_externe, nom, expected_identifiant_externe
    ):
        row = pd.Series({"identifiant_externe": identifiant_externe, "nom": nom})
        result = clean_identifiant_externe(row, None)
        assert result["identifiant_externe"] == expected_identifiant_externe

    def test_clean_identifiant_externe_raise(self):
        row = pd.Series({"id": None, "nom": None})
        with pytest.raises(ValueError) as erreur:
            clean_identifiant_externe(row, None)
        assert "id or nom" in str(erreur.value)


class TestCleanIdentifiantUnique:
    @pytest.mark.parametrize(
        (
            "identifiant_externe, acteur_type_code, source_code,"
            " expected_identifiant_unique"
        ),
        [
            ("12345", "commerce", "source", "source_12345"),
            (" 12345 ", "commerce", "source", "source_12345"),
            ("ABC123", "commerce", "source", "source_ABC123"),
            (" abc123 ", "commerce", "source", "source_abc123"),
            ("ABC123", "acteur_digital", "source", "source_ABC123_d"),
            (" abc123 ", "acteur_digital", "source", "source_abc123_d"),
        ],
    )
    def test_clean_identifiant_unique(
        self,
        identifiant_externe,
        acteur_type_code,
        source_code,
        expected_identifiant_unique,
    ):
        row = pd.Series(
            {
                "identifiant_externe": identifiant_externe,
                "source_code": source_code,
                "acteur_type_code": acteur_type_code,
            }
        )
        result = clean_identifiant_unique(row, None)
        assert result["identifiant_unique"] == expected_identifiant_unique

    def test_clean_identifiant_unique_failes(self):
        row = pd.Series(
            {
                "source_code": "source",
                "acteur_type_code": "commerce",
            }
        )
        with pytest.raises(ValueError) as erreur:
            clean_identifiant_unique(row, None)
        assert "identifiant_externe" in str(erreur.value)


class TestMergeSSCatColumns:
    @pytest.mark.parametrize(
        "row_columns, expected_produitsdechets_acceptes",
        [
            ({}, ""),
            ({"cat 1": "produit 1"}, "produit 1"),
            (
                {"cat 1": "produit 1", "cat 2": "produit 2", "cat 3": ""},
                "produit 1 | produit 2",
            ),
            (
                {"cat 1": "produit 1", "cat 2": "produit 2", "cat 3": "produit 3"},
                "produit 1 | produit 2 | produit 3",
            ),
        ],
    )
    def test_merge_sscat_columns(self, row_columns, expected_produitsdechets_acceptes):
        assert (
            merge_sous_categories_columns(
                pd.Series(row_columns),
                None,
            )["produitsdechets_acceptes"]
            == expected_produitsdechets_acceptes
        )


class TestCleanAdresse:
    # FIXME : Add tests
    # @patch("sources.tasks.transform.transform_df._get_address")
    pass


class TestCleanActeurserviceCodes:
    @pytest.mark.parametrize(
        "row_columns, expected_acteurservice_codes",
        [
            ({}, []),
            ({"point_dapport_de_service_reparation": True}, ["service_de_reparation"]),
            ({"point_de_reparation": True}, ["service_de_reparation"]),
            ({"point_dapport_pour_reemploi": True}, ["structure_de_collecte"]),
            (
                {"point_de_collecte_ou_de_reprise_des_dechets": True},
                ["structure_de_collecte"],
            ),
            (
                {
                    "point_dapport_de_service_reparation": True,
                    "point_de_reparation": True,
                    "point_dapport_pour_reemploi": True,
                    "point_de_collecte_ou_de_reprise_des_dechets": True,
                },
                ["service_de_reparation", "structure_de_collecte"],
            ),
        ],
    )
    def clean_acteurservice_codes(self, row_columns, expected_action_codes):
        result = clean_action_codes(pd.Series(row_columns), None)
        assert result["action_codes"] == expected_action_codes


class TestCleanActionCodes:
    @pytest.mark.parametrize(
        "row_columns, expected_action_codes",
        [
            ({}, []),
            ({"point_dapport_de_service_reparation": True}, ["reparer"]),
            ({"point_de_reparation": True}, ["reparer"]),
            ({"point_dapport_pour_reemploi": True}, ["donner"]),
            ({"point_de_collecte_ou_de_reprise_des_dechets": True}, ["trier"]),
            (
                {
                    "point_dapport_de_service_reparation": True,
                    "point_de_reparation": True,
                    "point_dapport_pour_reemploi": True,
                    "point_de_collecte_ou_de_reprise_des_dechets": True,
                },
                ["reparer", "donner", "trier"],
            ),
        ],
    )
    def test_clean_action_codes(self, row_columns, expected_action_codes):
        result = clean_action_codes(pd.Series(row_columns), None)
        assert result["action_codes"] == expected_action_codes


class TestCleanLabelCodes:
    @pytest.mark.parametrize(
        "value, expected_value",
        [
            (None, []),
            ("", []),
            ("label_et_bonus", ["label_et_bonus"]),
            ("label_et_bonus1|label_et_bonus2", ["label_et_bonus1", "label_et_bonus2"]),
            (
                "Agréé Bonus Réparation|label_et_bonus2",
                ["bonus_reparation", "label_et_bonus2"],
            ),
        ],
    )
    def test_clean_label_codes(self, value, expected_value, dag_config):
        dag_config.label_bonus_reparation = "bonus_reparation"
        result = clean_label_codes(
            pd.Series({"label_etou_bonus": value, "acteur_type_code": "commerce"}),
            dag_config=dag_config,
        )
        assert result["label_codes"] == expected_value

    def test_ess_label(self, dag_config):
        result = clean_label_codes(
            pd.Series(
                {"label_etou_bonus": "label_et_bonus", "acteur_type_code": "ess"}
            ),
            dag_config=dag_config,
        )

        assert result["label_codes"], ["ess", "label_et_bonus"]


class TestMergeAndCleanSouscategorieCodes:
    # FIXME : Add tests
    pass


class TestGetLatLngFromGeopoint:
    def test_get_latlng_from_geopoint(self):
        row = pd.Series({"_geopoint": "48.8588443,2.2943506"})
        result = get_latlng_from_geopoint(row, None)
        assert result["latitude"] == 48.8588443
        assert result["longitude"] == 2.2943506
