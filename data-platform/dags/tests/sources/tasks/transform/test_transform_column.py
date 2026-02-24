import numpy as np
import pandas as pd
import pytest
from sources.tasks.transform.exceptions import (
    ActeurTypeCodeError,
    BooleanValueWarning,
    CodePostalWarning,
    EmailWarning,
    OpeningHoursWarning,
    PublicAccueilliWarning,
    RepriseWarning,
    SirenWarning,
    SiretWarning,
    SousCategorieCodesError,
    UrlWarning,
)
from sources.tasks.transform.transform_column import (
    cast_eo_boolean_or_string_to_boolean,
    clean_acteur_type_code,
    clean_code_list,
    clean_code_postal,
    clean_email,
    clean_horaires_osm,
    clean_number,
    clean_public_accueilli,
    clean_reprise,
    clean_siren,
    clean_siret,
    clean_sous_categorie_codes,
    clean_sous_categorie_codes_sinoe,
    clean_url,
    convert_opening_hours,
    strip_lower_string,
    strip_string,
)


class TestCastEOBooleanOrStringToBoolean:
    @pytest.mark.parametrize(
        "value,expected_value",
        [
            (None, None),
            (False, False),
            (True, True),
            ("oui", True),
            ("Oui", True),
            (" Oui ", True),
            ("non", False),
            ("NON", False),
            (" NON ", False),
            ("no", False),
            ("yes", True),
            ("False", False),
            ("True", True),
            ("", None),
            (" ", None),
        ],
    )
    def test_cast_eo_boolean_or_string_to_boolean(
        self,
        value,
        expected_value,
    ):
        assert cast_eo_boolean_or_string_to_boolean(value, None) == expected_value

    @pytest.mark.parametrize(
        "value",
        [1.0, "fake"],
    )
    def test_cast_eo_boolean_or_string_to_boolean_warning(self, value):
        with pytest.raises(BooleanValueWarning):
            cast_eo_boolean_or_string_to_boolean(value, None)


class TestConvertOpeningHours:

    @pytest.mark.parametrize(
        "input_value, expected_output",
        [
            # chaine vide ou Nulle
            ("", ""),
            (None, ""),
            # chaines valides
            (
                "Mo-Fr 09:00-16:00",
                """lundi: 09:00 - 16:00
mardi: 09:00 - 16:00
mercredi: 09:00 - 16:00
jeudi: 09:00 - 16:00
vendredi: 09:00 - 16:00
samedi: Fermé
dimanche: Fermé""",
            ),
            (
                "Mo-Fr 09:00-12:00,14:00-17:00",
                """lundi: 09:00 - 12:00; 14:00 - 17:00
mardi: 09:00 - 12:00; 14:00 - 17:00
mercredi: 09:00 - 12:00; 14:00 - 17:00
jeudi: 09:00 - 12:00; 14:00 - 17:00
vendredi: 09:00 - 12:00; 14:00 - 17:00
samedi: Fermé
dimanche: Fermé""",
            ),
            (
                "Mo,Fr 09:00-12:00,15:00-17:00",
                """lundi: 09:00 - 12:00; 15:00 - 17:00
mardi: Fermé
mercredi: Fermé
jeudi: Fermé
vendredi: 09:00 - 12:00; 15:00 - 17:00
samedi: Fermé
dimanche: Fermé""",
            ),
            (
                "Mo,Tu,We 09:00-12:00",
                """lundi: 09:00 - 12:00
mardi: 09:00 - 12:00
mercredi: 09:00 - 12:00
jeudi: Fermé
vendredi: Fermé
samedi: Fermé
dimanche: Fermé""",
            ),
            (
                "24/7",
                """lundi: 00:00 - 23:59
mardi: 00:00 - 23:59
mercredi: 00:00 - 23:59
jeudi: 00:00 - 23:59
vendredi: 00:00 - 23:59
samedi: 00:00 - 23:59
dimanche: 00:00 - 23:59""",
            ),
            (
                "Mo 10:00-12:00,12:30-15:00; Tu-Fr 08:00-12:00,12:30-15:00;"
                " Sa 08:00-12:00",
                """lundi: 10:00 - 12:00; 12:30 - 15:00
mardi: 08:00 - 12:00; 12:30 - 15:00
mercredi: 08:00 - 12:00; 12:30 - 15:00
jeudi: 08:00 - 12:00; 12:30 - 15:00
vendredi: 08:00 - 12:00; 12:30 - 15:00
samedi: 08:00 - 12:00
dimanche: Fermé""",
            ),
        ],
    )
    def test_convert_opening_hours(self, input_value, expected_output):
        assert convert_opening_hours(input_value, None) == expected_output


class TestCleanSiren:
    @pytest.mark.parametrize(
        "siren, expected_siren",
        [
            (np.nan, ""),
            (pd.NA, ""),
            (None, ""),
            ("", ""),
            ("123456789", "123456789"),
            (" 123456789 ", "123456789"),
        ],
    )
    def test_clean_siren(self, siren, expected_siren):
        assert clean_siren(siren) == expected_siren

    @pytest.mark.parametrize(
        "siren",
        [
            "fake" "1234567890",
            "12345678",
        ],
    )
    def test_clean_siren_warning(self, siren):
        with pytest.raises(SirenWarning):
            clean_siren(siren)


class TestCleanSiret:
    @pytest.mark.parametrize(
        "siret, expected_siret",
        [
            (np.nan, ""),
            (pd.NA, ""),
            (None, ""),
            ("", ""),
            ("98765432109876", "98765432109876"),
            (" 98765432109876 ", "98765432109876"),
            ("8765432109876", "08765432109876"),
        ],
    )
    def test_clean_siret(self, siret, expected_siret):
        assert clean_siret(siret) == expected_siret

    @pytest.mark.parametrize(
        "siret",
        [
            "fake" "123456789012345",
            "AB123",
        ],
    )
    def test_clean_siret_warning(self, siret):
        with pytest.raises(SiretWarning):
            clean_siret(siret)


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
            ActeurTypeCodeError, match=f"Acteur type `{value}` not found in mapping :"
        ):
            clean_acteur_type_code(value, None)


class TestCleanPublicAccueilli:
    @pytest.mark.parametrize(
        "value, expected_value",
        [
            (None, ""),
            ("PARTICULIERS", "Particuliers"),
            ("Particuliers", "Particuliers"),
            ("DMA", "Particuliers"),
            ("DMA/PRO", "Particuliers et professionnels"),
            ("PRO", "Professionnels"),
            ("NP", ""),
            ("Particuliers et professionnels", "Particuliers et professionnels"),
        ],
    )
    def test_clean_public_accueilli(
        self,
        value,
        expected_value,
    ):

        assert clean_public_accueilli(value, None) == expected_value

    @pytest.mark.parametrize(
        "value",
        ["fake"],
    )
    def test_clean_public_accueilli_warning(self, value):
        with pytest.raises(PublicAccueilliWarning):
            clean_public_accueilli(value, None)


class TestCleanReprise:

    @pytest.mark.parametrize(
        "value,expected_value",
        [
            (None, ""),
            ("1 pour 0", "1 pour 0"),
            ("1 pour 1", "1 pour 1"),
            ("non", "1 pour 0"),
            ("oui", "1 pour 1"),
        ],
    )
    def test_clean_reprise(
        self,
        value,
        expected_value,
    ):
        assert clean_reprise(value, None) == expected_value

    @pytest.mark.parametrize(
        "value",
        ["fake"],
    )
    def test_clean_reprise_warning(self, value):
        with pytest.raises(RepriseWarning):
            clean_reprise(value, None)


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

    @pytest.mark.parametrize(
        "url", ["https://toto", "http://toto", "identifiantFacebook"]
    )
    def test_clean_url_warning(self, url):
        with pytest.raises(UrlWarning):
            clean_url(url, None)


class TestCleanEmail:
    @pytest.mark.parametrize(
        "email, expected_email",
        [
            (None, ""),
            ("", ""),
            ("fake@example.com", "fake@example.com"),
            (" fake@example.com ", "fake@example.com"),
            (
                "prenom.de-mon_nom@ex-am_ple.com.fr",
                "prenom.de-mon_nom@ex-am_ple.com.fr",
            ),
        ],
    )
    def test_clean_email(self, email, expected_email):
        assert clean_email(email, None) == expected_email

    @pytest.mark.parametrize("email", ["fake", "@example.com"])
    def test_clean_email_warning(self, email):
        with pytest.raises(EmailWarning):
            clean_email(email, None)


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

    @pytest.mark.parametrize("cp", ["123456", "123", "Paris"])
    def test_clean_code_postal_warning(self, cp):
        with pytest.raises(CodePostalWarning):
            clean_code_postal(cp, None)


class TestCleanHorairesOsm:
    @pytest.mark.parametrize(
        "horaires_osm, expected_horaires_osm",
        [
            ("", ""),
            ("12h30-15h30", "12:30-15:30"),
            ("Mo-Fr 12h30-15h30,16h30-18h30", "Mo-Fr 12:30-15:30,16:30-18:30"),
            (
                "Mo-Fr 12h30-15h30,16h30-18h30 ; We 12h30-15h30",
                "Mo-Fr 12:30-15:30,16:30-18:30 ; We 12:30-15:30",
            ),
        ],
    )
    def test_clean_horaires_osm(self, horaires_osm, expected_horaires_osm):
        assert clean_horaires_osm(horaires_osm, None) == expected_horaires_osm

    def test_clean_horaires_osm_warning(self):
        with pytest.raises(OpeningHoursWarning):
            clean_horaires_osm("fake", None)


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
                ["sscat1", "sscat2", "sscat1"],  # works with a list
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
    def test_clean_sous_categorie_codes(
        self, sscat_list, product_mapping, expected_output, dag_config
    ):
        dag_config.product_mapping = product_mapping
        result = clean_sous_categorie_codes(sscat_list, dag_config)
        assert sorted(result) == sorted(expected_output)

    def test_clean_sous_categorie_codes_raise(self, dag_config):
        dag_config.product_mapping = {"sscat1": 1.0}
        with pytest.raises(SousCategorieCodesError):
            clean_sous_categorie_codes("sscat1", dag_config)


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
    def test_clean_sous_categorie_codes_sinoe(
        self, sscats, dechet_mapping, product_mapping, expected_output, dag_config
    ):
        # Mock the DAGConfig
        dag_config.dechet_mapping = dechet_mapping
        dag_config.product_mapping = product_mapping

        result = clean_sous_categorie_codes_sinoe(sscats, dag_config)
        assert sorted(result) == sorted(expected_output)


class TestCleanCodeList:
    @pytest.mark.parametrize(
        "input_codes, expected_output",
        [
            (None, []),
            ("", []),
            ("code1", ["code1"]),
            ("CODE1", ["code1"]),
            ("code1|code2", ["code1", "code2"]),
            ("code1 | code2", ["code1", "code2"]),
            ("  code1  |  code2  ", ["code1", "code2"]),
            ("code1||code2", ["code1", "code2"]),
            ("code1| |code2", ["code1", "code2"]),
            ("CODE1|Code2|code3", ["code1", "code2", "code3"]),
        ],
    )
    def test_clean_code_list(self, input_codes, expected_output):
        assert clean_code_list(input_codes, None) == expected_output
