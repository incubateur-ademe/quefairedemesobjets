import pandas as pd
import pytest
from sources.tasks.transform.transform_df import (
    _parse_float,
    clean_acteur_service_codes,
    clean_action_codes,
    clean_adresse,
    clean_identifiant_externe,
    clean_identifiant_unique,
    clean_label_codes,
    clean_proposition_services,
    clean_siret_and_siren,
    clean_telephone,
    compute_location,
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
                        "label_codes": [
                            ["Plastic Box", "Metal", "Aàèë l'test"],
                            ["Plastic Box", "Metal", "Aàèë l'test"],
                        ],
                        "other_column": ["A", "B"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "label_codes": [["Aàèë l'test", "Metal", "Plastic Box"]],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "label_codes": [
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
                        "label_codes": [
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
                        "label_codes": [
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
                        "label_codes": [["Glass", "Metal", "Paper", "Plastic"]],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 2, 3, 3, 3],
                        "label_codes": [
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
                        "label_codes": [
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
    def test_merge_duplicates_list(self, df, expected_df):

        result_df = merge_duplicates(
            df,
            group_column="identifiant_unique",
            merge_as_list_columns=["label_codes"],
            merge_as_proposition_service_columns=[],
        )

        result_df = result_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )
        expected_df = expected_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )

        pd.testing.assert_frame_equal(result_df, expected_df)

    @pytest.mark.parametrize(
        "df, expected_df",
        [
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "proposition_service_codes": [[], []],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "proposition_service_codes": [[]],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                }
                            ],
                            [],
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                }
                            ]
                        ],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                }
                            ],
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                }
                            ],
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                }
                            ]
                        ],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat2"],
                                }
                            ],
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1"],
                                }
                            ],
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                }
                            ]
                        ],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                }
                            ],
                            [
                                {
                                    "action": "action2",
                                    "sous_categories": ["sscat1"],
                                }
                            ],
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2"],
                                },
                                {
                                    "action": "action2",
                                    "sous_categories": ["sscat1"],
                                },
                            ],
                        ],
                    }
                ),
            ),
            # Validation of the order while merge duplicates
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action3",
                                    "sous_categories": ["sscat2", "sscat1"],
                                },
                                {
                                    "action": "action2",
                                    "sous_categories": ["sscat3", "sscat2"],
                                },
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat3"],
                                },
                            ],
                            [
                                {
                                    "action": "action2",
                                    "sous_categories": ["sscat1", "sscat3"],
                                },
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat2", "sscat3"],
                                },
                                {
                                    "action": "action3",
                                    "sous_categories": ["sscat3", "sscat2"],
                                },
                            ],
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "proposition_service_codes": [
                            [
                                {
                                    "action": "action1",
                                    "sous_categories": ["sscat1", "sscat2", "sscat3"],
                                },
                                {
                                    "action": "action2",
                                    "sous_categories": ["sscat1", "sscat2", "sscat3"],
                                },
                                {
                                    "action": "action3",
                                    "sous_categories": ["sscat1", "sscat2", "sscat3"],
                                },
                            ],
                        ],
                    }
                ),
            ),
        ],
    )
    def test_merge_duplicates_ps_dict(self, df, expected_df):

        result_df = merge_duplicates(
            df,
            group_column="identifiant_unique",
            merge_as_list_columns=[],
            merge_as_proposition_service_columns=["proposition_service_codes"],
        )

        result_df = result_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )
        expected_df = expected_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )

        pd.testing.assert_frame_equal(result_df, expected_df)


class TestCleanPropositionServiceCodes:
    @pytest.mark.parametrize(
        "action_codes, sous_categorie_codes, expected_proposition_service_codes",
        [
            ([], [], []),
            (
                ["action1"],
                ["sscat1"],
                [{"action": "action1", "sous_categories": ["sscat1"]}],
            ),
            (
                ["action1", "action2"],
                ["sscat1", "sscat2"],
                [
                    {"action": "action1", "sous_categories": ["sscat1", "sscat2"]},
                    {"action": "action2", "sous_categories": ["sscat1", "sscat2"]},
                ],
            ),
            (
                ["action3", "action1", "action2"],
                ["sscat3", "sscat2", "sscat1"],
                [
                    {
                        "action": "action1",
                        "sous_categories": ["sscat1", "sscat2", "sscat3"],
                    },
                    {
                        "action": "action2",
                        "sous_categories": ["sscat1", "sscat2", "sscat3"],
                    },
                    {
                        "action": "action3",
                        "sous_categories": ["sscat1", "sscat2", "sscat3"],
                    },
                ],
            ),
        ],
    )
    def test_clean_proposition_service_codes(
        self, action_codes, sous_categorie_codes, expected_proposition_service_codes
    ):
        result = clean_proposition_services(
            pd.Series(
                {
                    "action_codes": action_codes,
                    "sous_categorie_codes": sous_categorie_codes,
                }
            ),
            None,
        )
        assert result["proposition_service_codes"] == expected_proposition_service_codes


class TestCleanTelephone:
    @pytest.mark.parametrize(
        "phone_number, code_postal, expected_phone_number",
        [
            (None, None, ""),
            (pd.NA, None, ""),
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
            (None, None, "", ""),
            ("12345678901234", None, "12345678901234", "123456789"),
            (" 12345678901234 ", None, "12345678901234", "123456789"),
            (None, "123456789", "", "123456789"),
            ("98765432109876", "987654321", "98765432109876", "987654321"),
            (" 98765432109876 ", " 987654321 ", "98765432109876", "987654321"),
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
        "identifiant_externe, acteur_type_code, nom, expected_identifiant_externe",
        [
            (None, "commerce", "nom", "nom"),
            (None, "commerce", "nom-nom nom_nom__nom", "nomnom_nom_nom_nom"),
            ("12345", "commerce", "12345", "12345"),
            (" 12345 ", "commerce", "12345", "12345"),
            ("ABC123", "commerce", "ABC123", "ABC123"),
            (" abc123 ", "commerce", "abc123", "abc123"),
            (None, "acteur_digital", "nom", "nom_d"),
            ("ABC123", "acteur_digital", "ABC123", "ABC123_d"),
            (" abc123 ", "acteur_digital", "abc123", "abc123_d"),
        ],
    )
    def test_clean_identifiant_externe(
        self, identifiant_externe, acteur_type_code, nom, expected_identifiant_externe
    ):
        row = pd.Series(
            {
                "identifiant_externe": identifiant_externe,
                "acteur_type_code": acteur_type_code,
                "nom": nom,
            }
        )
        result = clean_identifiant_externe(row, None)
        assert result["identifiant_externe"] == expected_identifiant_externe

    def test_clean_identifiant_externe_raise(self):
        row = pd.Series({"id": None, "nom": None})
        with pytest.raises(ValueError) as erreur:
            clean_identifiant_externe(row, None)
        assert "id or nom" in str(erreur.value)


class TestCleanIdentifiantUnique:
    @pytest.mark.parametrize(
        ("identifiant_externe, source_code, expected_identifiant_unique"),
        [
            (12345, "source", "source_12345"),
            ("12345", "source", "source_12345"),
            (" 12345 ", "source", "source_12345"),
            ("ABC123", "source", "source_ABC123"),
            (" abc123 ", "source", "source_abc123"),
        ],
    )
    def test_clean_identifiant_unique(
        self,
        identifiant_externe,
        source_code,
        expected_identifiant_unique,
    ):
        row = pd.Series(
            {
                "identifiant_externe": identifiant_externe,
                "source_code": source_code,
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
    @pytest.mark.parametrize(
        "adresse_format_ban, expected_adresse",
        [
            (
                "123 Rue de Paris 75001 Paris",
                {
                    "adresse": "123 Rue de Paris",
                    "code_postal": "75001",
                    "ville": "Paris",
                },
            ),
            (
                " 123 Rue de Paris  75001  Paris ",
                {
                    "adresse": "123 Rue de Paris",
                    "code_postal": "75001",
                    "ville": "Paris",
                },
            ),
            (
                "75001 Paris",
                {
                    "adresse": "",
                    "code_postal": "75001",
                    "ville": "Paris",
                },
            ),
            (
                " 123 Rue de Paris 75001 Paris CEDEX 01123",
                {
                    "adresse": "123 Rue de Paris",
                    "code_postal": "75001",
                    "ville": "Paris",
                },
            ),
            (
                "Rue des Balmes,38540,HEYRIEUX",
                {
                    "adresse": "Rue des Balmes",
                    "code_postal": "38540",
                    "ville": "Heyrieux",
                },
            ),
            (
                "Rue des Balmes;38540;HEYRIEUX",
                {
                    "adresse": "Rue des Balmes",
                    "code_postal": "38540",
                    "ville": "Heyrieux",
                },
            ),
            (
                "Rue des Balmes - 38540 - HEYRIEUX",
                {
                    "adresse": "Rue des Balmes",
                    "code_postal": "38540",
                    "ville": "Heyrieux",
                },
            ),
            (
                "- 31660 avenue de Maurin, 34076 Montpellier",
                {
                    "adresse": "31660 avenue de Maurin",
                    "code_postal": "34076",
                    "ville": "Montpellier",
                },
            ),
            (
                "12 Av. du 14 Juillet 1789, 57180 Terville",
                {
                    "adresse": "12 Av. du 14 Juillet 1789",
                    "code_postal": "57180",
                    "ville": "Terville",
                },
            ),
        ],
    )
    def test_clean_adresse_without_ban(
        self, adresse_format_ban, expected_adresse, dag_config
    ):
        dag_config.validate_address_with_ban = False
        row = pd.Series({"adresse_format_ban": adresse_format_ban})
        assert dict(clean_adresse(row, dag_config)) == expected_adresse

    def test_clean_adresse_with_ban(self, dag_config, mocker):
        def _get_address(_):
            # Mock implementation of _get_address
            return "Mock Address", "Mock Postal Code", "Mock City"

        mocker.patch(
            "sources.tasks.transform.transform_df._get_address",
            side_effect=_get_address,
        )
        dag_config.validate_address_with_ban = True
        row = pd.Series({"adresse_format_ban": "fake adresse"})
        assert dict(clean_adresse(row, dag_config)) == {
            "adresse": "Mock Address",
            "code_postal": "Mock Postal Code",
            "ville": "Mock City",
        }


class TestCleanActeurserviceCodes:
    @pytest.mark.parametrize(
        "row_columns, expected_acteur_service_codes",
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
    def test_clean_acteur_service_codes(
        self, row_columns, expected_acteur_service_codes
    ):
        result = clean_acteur_service_codes(pd.Series(row_columns), None)
        assert result["acteur_service_codes"] == expected_acteur_service_codes


class TestCleanActionCodes:
    @pytest.mark.parametrize(
        "row_columns, expected_action_codes, expected_action_codes_returnable_objects",
        [
            ({}, [], []),
            ({"point_dapport_de_service_reparation": True}, ["reparer"], ["reparer"]),
            ({"point_de_reparation": True}, ["reparer"], ["reparer"]),
            ({"point_dapport_pour_reemploi": True}, ["donner"], ["rapporter"]),
            (
                {"point_de_collecte_ou_de_reprise_des_dechets": True},
                ["trier"],
                ["trier"],
            ),
            (
                {
                    "point_dapport_de_service_reparation": True,
                    "point_de_reparation": True,
                    "point_dapport_pour_reemploi": True,
                    "point_de_collecte_ou_de_reprise_des_dechets": True,
                },
                ["reparer", "donner", "trier"],
                ["reparer", "rapporter", "trier"],
            ),
        ],
    )
    def test_clean_action_codes(
        self,
        row_columns,
        expected_action_codes,
        expected_action_codes_returnable_objects,
        dag_config,
    ):
        dag_config.returnable_objects = False
        result = clean_action_codes(pd.Series(row_columns), dag_config)
        assert result["action_codes"] == expected_action_codes
        dag_config.returnable_objects = True
        result = clean_action_codes(pd.Series(row_columns), dag_config)
        assert result["action_codes"] == expected_action_codes_returnable_objects


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


class TestGetLatLngFromGeopoint:
    def test_get_latlng_from_geopoint(self):
        row = pd.Series({"_geopoint": "48.8588443,2.2943506"})
        result = get_latlng_from_geopoint(row, None)
        assert result["latitude"] == 48.8588443
        assert result["longitude"] == 2.2943506


PARIS_LOCATION = (
    "0101000000a835cd3b4ed1024076e09c11a56d4840"  # pragma: allowlist secret
)


LONDON_LOCATION = (
    "0101000000ebe2361ac05bc0bfc5feb27bf2c04940"  # pragma: allowlist secret
)


class TestComputeLocation:

    @pytest.mark.parametrize(
        "latitude, longitude, expected_location",
        [
            (48.8566, 2.3522, PARIS_LOCATION),
            ("48.8566", "2.3522", PARIS_LOCATION),
            (51.5074, -0.1278, LONDON_LOCATION),
            (None, None, None),  # Missing lat and long
        ],
    )
    def test_compute_location(self, latitude, longitude, expected_location):

        result = compute_location(
            pd.Series({"latitude": latitude, "longitude": longitude}), None
        )
        assert result["location"] == expected_location


class TestParseFloat:
    def test_parse_float_with_french_decimal(self):
        assert _parse_float("1234,56") == 1234.56
        assert _parse_float("-1234,56") == -1234.56
        assert _parse_float("0,0") == 0
        assert _parse_float("1,234") == 1.234

    def test_parse_float_with_trailing_comma(self):
        assert _parse_float("1234,") == 1234.0
        assert _parse_float("1234,56,") == 1234.56

    def test_parse_float_with_valid_float(self):
        assert _parse_float(1234.56) == 1234.56
        assert _parse_float(-1234.56) == -1234.56

    def test_parse_float_with_nan(self):
        assert _parse_float(float("nan")) is None

    def test_parse_float_with_none(self):
        assert _parse_float(None) is None

    def test_parse_float_with_invalid_string(self):
        assert _parse_float("abc") is None
        assert _parse_float("1234abc") is None
        assert _parse_float("12,34,56") is None
