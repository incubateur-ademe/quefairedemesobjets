import pandas as pd
import pytest
from sources.tasks.transform.transform_df import (
    clean_action_codes,
    clean_label_codes,
    clean_telephone,
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
                        "produitsdechets_acceptes": [
                            " Plastic Box | Metal | Aàèë l'test",
                            " Plastic Box | Metal | Aàèë l'test",
                        ],
                        "other_column": ["A", "B"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["Aàèë l'test|Metal|Plastic Box"],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
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
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
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
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
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
                        "produitsdechets_acceptes": ["Glass|Metal|Paper|Plastic"],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 2, 3, 3, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                            "Glass|Plastic",
                            "Plastic|Metal",
                            "Metal",
                        ],
                        "other_column": ["A", "B", "C", "D", "E", "F"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Glass|Metal|Plastic",
                            "Paper",
                            "Glass|Metal|Plastic",
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
    # FIXME : Add tests
    pass


class TestCleanIdentifiantExterne:
    # FIXME : Add tests
    pass


class TestCleanIdentifiantUnique:
    # FIXME : Add tests
    pass


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
            ("label_et_bonus", ["label_et_bonus"]),
            ("label_et_bonus1|label_et_bonus2", ["label_et_bonus1", "label_et_bonus2"]),
            (
                "Agréé Bonus Réparation|label_et_bonus2",
                ["bonus_reparation", "label_et_bonus2"],
            ),
        ],
    )
    def test_clean_label_codes(self, value, expected_value, dag_config):
        dag_config.label_bonus_reparation = ("bonus_reparation",)
        result = clean_label_codes(
            pd.Series({"label_etou_bonus": value, "acteur_type_code": "commerce"}),
            dag_config=dag_config,
        )

        assert result["label_codes"], expected_value

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
