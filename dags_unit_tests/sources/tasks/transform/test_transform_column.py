import numpy as np
import pandas as pd
import pytest
from sources.tasks.transform.transform_column import (
    cast_eo_boolean_or_string_to_boolean,
    clean_code_postal,
    clean_number,
    clean_public_accueilli,
    clean_reprise,
    clean_siren,
    clean_siret,
    clean_souscategorie_codes,
    clean_url,
    convert_opening_hours,
    strip_string,
)


class TestCastEOBooleanOrStringToBoolean:
    @pytest.mark.parametrize(
        "value,expected_value",
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
    def test_cast_eo_boolean_or_string_to_boolean(
        self,
        value,
        expected_value,
    ):

        assert cast_eo_boolean_or_string_to_boolean(value, None) == expected_value


class TestConvertOpeningHours:

    @pytest.mark.parametrize(
        "input_value, expected_output",
        [
            # chaine vide ou Nulle
            ("", ""),
            (None, ""),
            (pd.NA, ""),
            (np.nan, ""),
            # chaines valides
            ("Mo-Fr 09:00-16:00", "du lundi au vendredi de 09h00 à 16h00"),
            (
                "Mo-Fr 09:00-12:00,14:00-17:00",
                "du lundi au vendredi de 09h00 à 12h00 et de 14h00 à 17h00",
            ),
            # TODO : à implémenter
            # (
            #     "Mo,Fr 09:00-12:00,15:00-17:00",
            #     "le lundi et le vendredi de 09h00 à 12h00 et de 15h00 à 17h00"
            # ),
            # (
            #     "Mo,Tu,We 09:00-12:00",
            #     "le lundi, mardi et le mercredi de 09h00 à 12h00"
            # ),
        ],
    )
    def test_convert_opening_hours(self, input_value, expected_output):
        assert convert_opening_hours(input_value, None) == expected_output


class TestCleanSiren:
    @pytest.mark.parametrize(
        "siren, expected_siren",
        [
            (np.nan, None),
            (pd.NA, None),
            (None, None),
            ("", None),
            ("1234567890", None),
            ("123456789", "123456789"),
            ("12345678", None),
        ],
    )
    def test_clean_siren(self, siren, expected_siren):
        assert clean_siren(siren) == expected_siren


class TestCleanSiret:
    @pytest.mark.parametrize(
        "siret, expected_siret",
        [
            (np.nan, None),
            (pd.NA, None),
            (None, None),
            ("", None),
            ("123456789012345", None),
            ("98765432109876", "98765432109876"),
            ("8765432109876", "08765432109876"),
            ("AB123", None),
        ],
    )
    def test_clean_siret(self, siret, expected_siret):
        assert clean_siret(siret) == expected_siret


class TestCleanNumber:
    @pytest.mark.parametrize(
        "number, expected_number",
        [
            (None, ""),
            (np.nan, ""),
            (pd.NA, ""),
            ("12345.0", "12345"),
            ("12345.67", "1234567"),
            ("+33 1 23 45 67 89", "+33123456789"),
            ("(123) 456-7890", "1234567890"),
            ("123-456-7890", "1234567890"),
            ("123 456 7890", "1234567890"),
            ("123.456.7890", "1234567890"),
            ("1234567890", "1234567890"),
            ("12345", "12345"),
            ("", ""),
        ],
    )
    def test_clean_number(self, number, expected_number):
        assert clean_number(number) == expected_number


class TestStripString:

    @pytest.mark.parametrize(
        "input, output",
        [
            (None, ""),
            (pd.NA, ""),
            (np.nan, ""),
            (" ", ""),
            (75001, "75001"),
            (" adresse postale ", "adresse postale"),
        ],
    )
    def test_strip_string(self, input, output):
        assert strip_string(input, None) == output


class TestCleanActeurTypeCode:
    # FIXME : Add tests
    pass


class TestCleanPublicAccueilli:
    @pytest.mark.parametrize(
        "value, expected_value",
        [
            (None, None),
            ("fake", None),
            ("PARTICULIERS", "Particuliers"),
            ("Particuliers", "Particuliers"),
            ("DMA", "Particuliers"),
            ("DMA/PRO", "Particuliers et professionnels"),
            ("PRO", "Professionnels"),
            ("NP", None),
            ("Particuliers et professionnels", "Particuliers et professionnels"),
        ],
    )
    def test_clean_public_accueilli(
        self,
        value,
        expected_value,
    ):

        assert clean_public_accueilli(value, None) == expected_value


class TestCleanReprise:

    @pytest.mark.parametrize(
        "value,expected_value",
        [
            (None, None),
            ("1 pour 0", "1 pour 0"),
            ("1 pour 1", "1 pour 1"),
            ("non", "1 pour 0"),
            ("oui", "1 pour 1"),
            ("fake", None),
        ],
    )
    def test_clean_reprise(
        self,
        value,
        expected_value,
    ):
        assert clean_reprise(value, None) == expected_value


class TestCleanUrl:
    @pytest.mark.parametrize(
        "url, expected_url",
        [
            (None, ""),
            (pd.NA, ""),
            ("", ""),
            ("http://example.com", "http://example.com"),
            ("https://example.com", "https://example.com"),
            ("example.com", "https://example.com"),
        ],
    )
    def test_clean_url(self, url, expected_url):
        assert clean_url(url, None) == expected_url


class TestCleanCodePostal:
    @pytest.mark.parametrize(
        "cp, expected_cp",
        [
            (None, ""),
            ("", ""),
            ("75001", "75001"),
            ("7501", "07501"),
        ],
    )
    def test_clean_code_postal(self, cp, expected_cp):
        assert clean_code_postal(cp, None) == expected_cp


class TestCleanSousCategorieCodes:
    @pytest.mark.parametrize(
        "sscat_list, product_mapping, expected_output",
        [
            (None, {}, []),
            ("", {}, []),
            ("sscat1", {"sscat1": "mapped1"}, ["mapped1"]),
            (
                "sscat1|sscat2",
                {"sscat1": "mapped1", "sscat2": "mapped2"},
                ["mapped1", "mapped2"],
            ),
            (
                " sscat1  |  sscat2  |  | ",
                {"sscat1": "mapped1", "sscat2": "mapped2"},
                ["mapped1", "mapped2"],
            ),
            (
                "sscat1|sscat2|sscat1",
                {"sscat1": "mapped1", "sscat2": "mapped2"},
                ["mapped1", "mapped2"],
            ),
            (
                "sscat1|sscat2",
                {"sscat1": ["mapped1a", "mapped1b"], "sscat2": "mapped2"},
                ["mapped1a", "mapped1b", "mapped2"],
            ),
        ],
    )
    def test_clean_souscategorie_codes(
        self, sscat_list, product_mapping, expected_output, dag_config
    ):
        dag_config.product_mapping = product_mapping
        result = clean_souscategorie_codes(sscat_list, dag_config)
        assert sorted(result) == sorted(expected_output)

    def test_clean_souscategorie_codes_raise(self, dag_config):
        dag_config.product_mapping = {"sscat1": 1.0}
        with pytest.raises(ValueError):
            clean_souscategorie_codes("sscat1", dag_config)


class TestCleanSouscategorieCodesSinoe:
    # FIXME : Add tests
    pass

    # @pytest.mark.parametrize("produitsdechets_acceptes", (None, "NP|01.22"))
    # def test_produitsdechets_acceptes_exclude_entries_not_mapped(
    #     self,
    #     product_mapping,
    #     dechet_mapping,
    #     produitsdechets_acceptes,
    # ):
    #     df_normalised = pd.DataFrame(
    #         {
    #             "identifiant_externe": ["DECHET_2"],
    #             "ANNEE": [2024],
    #             "_geopoint": ["48.4812237361283,3.120109493179493"],
    #             "produitsdechets_acceptes": [produitsdechets_acceptes],
    #             "public_accueilli": ["DMA"],
    #         },
    #     )

    #     df = df_normalize_sinoe(
    #         df=df_normalised,
    #         product_mapping=product_mapping,
    #         dechet_mapping=dechet_mapping,
    #     )
    #     assert len(df) == 0

    # @pytest.mark.parametrize(
    #     "produitsdechets_acceptes, produitsdechets_acceptes_expected",
    #     (
    #         [
    #             "01.1|07.25|07.6",
    #             ["Solvants usés", "Papiers cartons mêlés triés", "Déchets textiles"],
    #         ],
    #         ["07.6", ["Déchets textiles"]],
    #     ),
    # )
    # def test_produitsdechets_acceptes_convert_dechet_codes_to_our_codes(
    #     self,
    #     product_mapping,
    #     dechet_mapping,
    #     produitsdechets_acceptes,
    #     produitsdechets_acceptes_expected,
    # ):
    #     df_normalised = pd.DataFrame(
    #         {
    #             "identifiant_externe": ["DECHET_2"],
    #             "ANNEE": [2024],
    #             "_geopoint": ["48.4812237361283,3.120109493179493"],
    #             "produitsdechets_acceptes": [produitsdechets_acceptes],
    #             "public_accueilli": ["DMA"],
    #         },
    #     )
    #     df = df_normalize_sinoe(
    #         df=df_normalised,
    #         product_mapping=product_mapping,
    #         dechet_mapping=dechet_mapping,
    #     )
    #     assert (
    #         df.iloc[0]["produitsdechets_acceptes"] ==
    # produitsdechets_acceptes_expected
    #     )
