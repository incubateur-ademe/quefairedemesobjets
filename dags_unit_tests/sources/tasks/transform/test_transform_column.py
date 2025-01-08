import numpy as np
import pandas as pd
import pytest
from sources.tasks.transform.transform_column import (
    cast_eo_boolean_or_string_to_boolean,
    clean_acteur_type_code,
    clean_code_postal,
    clean_number,
    clean_public_accueilli,
    clean_reprise,
    clean_siren,
    clean_siret,
    clean_souscategorie_codes,
    clean_souscategorie_codes_sinoe,
    clean_url,
    convert_opening_hours,
    strip_lower_string,
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


class TestStriplowerString:

    @pytest.mark.parametrize(
        "input, output",
        [
            (None, ""),
            (pd.NA, ""),
            (np.nan, ""),
            (" ", ""),
            (75001, "75001"),
            (" adresse postale ", "adresse postale"),
            ("AdreSse posTale", "adresse postale"),
            (" AdreSse posTale ", "adresse postale"),
        ],
    )
    def test_strip_lower_string(self, input, output):
        assert strip_lower_string(input, None) == output


class TestCleanActeurTypeCode:
    @pytest.mark.parametrize(
        "value, expected_code",
        [
            ("solution en ligne (site web, app. mobile)", "acteur_digital"),
            ("artisan, commerce independant", "artisan"),
            (
                "magasin / franchise, enseigne commerciale / distributeur /"
                " point de vente",
                "commerce",
            ),
            ("point d'apport volontaire publique", "pav_public"),
            ("association, entreprise de l'economie sociale et solidaire (ess)", "ess"),
            ("etablissement de sante", "ets_sante"),
            ("decheterie", "decheterie"),
            ("point d'apport volontaire prive", "pav_prive"),
            ("plateforme inertes", "plateforme_inertes"),
            (
                "magasin / franchise, enseigne commerciale / distributeur / "
                "point de vente / franchise, enseigne commerciale / distributeur /"
                " point de vente",
                "commerce",
            ),
            ("point d'apport volontaire ephemere / ponctuel", "pav_ponctuel"),
            (" Dèchëtérie ", "decheterie"),
        ],
    )
    def test_clean_acteur_type_code(self, value, expected_code):
        assert clean_acteur_type_code(value, None) == expected_code

    @pytest.mark.parametrize(
        "value",
        [
            ("unknown type"),
            ("another unknown type"),
        ],
    )
    def test_clean_acteur_type_code_invalid(self, value):
        with pytest.raises(
            ValueError, match=f"Acteur type `{value}` not found in mapping"
        ):
            clean_acteur_type_code(value, None)


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
    @pytest.mark.parametrize(
        "sscats, dechet_mapping, product_mapping, expected_output",
        [
            (None, {}, {}, []),
            ("", {}, {}, []),
            (
                "01.3|02.31",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped1": "product1", "mapped2": "product2"},
                ["product1", "product2"],
            ),
            (
                "01.3|02.31|01.3",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped1": "product1", "mapped2": "product2"},
                ["product1", "product2"],
            ),
            (
                "01.3|02.31",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped1": "product1"},
                ["product1"],
            ),
            (
                "01.3|02.31",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped2": "product2"},
                ["product2"],
            ),
            ("01.3|02.31", {"01.3": "mapped1", "02.31": "mapped2"}, {}, []),
            (
                "01.3|nan|02.31",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped1": "product1", "mapped2": "product2"},
                ["product1", "product2"],
            ),
            (
                "01.3|np|02.31",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped1": "product1", "mapped2": "product2"},
                ["product1", "product2"],
            ),
            (
                "01.3|None|02.31",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped1": "product1", "mapped2": "product2"},
                ["product1", "product2"],
            ),
            (
                "01.3 | | 02.31",
                {"01.3": "mapped1", "02.31": "mapped2"},
                {"mapped1": "product1", "mapped2": "product2"},
                ["product1", "product2"],
            ),
        ],
    )
    def test_clean_souscategorie_codes_sinoe(
        self, sscats, dechet_mapping, product_mapping, expected_output, dag_config
    ):
        # Mock the DAGConfig
        dag_config.dechet_mapping = dechet_mapping
        dag_config.product_mapping = product_mapping

        result = clean_souscategorie_codes_sinoe(sscats, dag_config)
        assert sorted(result) == sorted(expected_output)
