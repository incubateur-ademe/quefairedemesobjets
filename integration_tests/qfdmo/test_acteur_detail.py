import pytest
from bs4 import BeautifulSoup

from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    LabelQualiteFactory,
    SourceFactory,
)


@pytest.fixture
def get_response(client):
    def _get_response(identifiant_unique):
        url = f"/adresse/{identifiant_unique}"
        response = client.get(url)
        assert response.status_code == 200
        return response, BeautifulSoup(response.content, "html.parser")

    return _get_response


@pytest.mark.django_db
class TestDisplaySource:
    def test_display_no_source(self, get_response):
        adresse = DisplayedActeurFactory()
        response, _ = get_response(adresse.identifiant_unique)
        assert response.context["display_sources_panel"] is False

    def test_display_one_source(self, get_response):
        adresse = DisplayedActeurFactory()
        adresse.sources.add(SourceFactory(afficher=True))
        response, _ = get_response(adresse.identifiant_unique)
        assert response.context["display_sources_panel"] is True


@pytest.mark.django_db
class TestDisplayLabel:
    @pytest.mark.parametrize(
        "label_setup, expected_text, should_display",
        [
            ([], None, False),
            (
                [("ess", "Enseigne de l'économie sociale et solidaire", True)],
                "Enseigne de l'économie sociale et solidaire",
                False,
            ),
            ([("label", "Mon label", False)], "Mon label", True),
            (
                [("label1", "Mon label 1", False), ("label2", "Mon label 2", False)],
                "Cet établissement dispose de plusieurs labels",
                True,
            ),
            (
                [("label", "Mon label", False, True)],
                "Éligible au bonus réparation",
                True,
            ),
        ],
    )
    def test_display_labels(
        self, get_response, label_setup, expected_text, should_display
    ):
        adresse = DisplayedActeurFactory()
        for code, libelle, type_enseigne, *bonus in label_setup:
            adresse.labels.add(
                LabelQualiteFactory(
                    code=code,
                    libelle=libelle,
                    type_enseigne=type_enseigne,
                    bonus=bonus[0] if bonus else False,
                )
            )

        response, soup = get_response(adresse.identifiant_unique)
        assert response.context["display_labels_panel"] == should_display
        label_tag = soup.find(attrs={"data-testid": "acteur-detail-labels"})
        if expected_text:
            assert label_tag and expected_text in label_tag.text
        else:
            assert label_tag is None


@pytest.mark.django_db
class TestAboutPanel:
    def assert_about_panel_text(self, soup, expected_text, text_is_expected):
        wrapper = soup.find(attrs={"data-testid": "acteur-detail-about-panel"})
        assert wrapper is not None
        if text_is_expected:
            assert expected_text in wrapper.text
        else:
            assert expected_text not in wrapper.text

    @pytest.mark.parametrize(
        "uniquement_sur_rdv", [True, False], ids=["With RDV", "Without RDV"]
    )
    def test_display_rdv_message(self, get_response, uniquement_sur_rdv):
        adresse = DisplayedActeurFactory()
        expected_text = "📆 Les services de cet établissement ne sont disponibles"
        " que sur rendez-vous."
        adresse.uniquement_sur_rdv = uniquement_sur_rdv
        adresse.save()

        response, soup = get_response(adresse.identifiant_unique)
        self.assert_about_panel_text(soup, expected_text, uniquement_sur_rdv)

    @pytest.mark.parametrize(
        "exclusivite_de_reprisereparation",
        [True, False],
        ids=["Exclusive Reparation", "Non-exclusive Reparation"],
    )
    def test_display_reparation_message(
        self, get_response, exclusivite_de_reprisereparation
    ):
        adresse = DisplayedActeurFactory()
        expected_text = "Cet établissement ne répare que les produits de ses marques."
        adresse.exclusivite_de_reprisereparation = exclusivite_de_reprisereparation
        adresse.save()

        response, soup = get_response(adresse.identifiant_unique)
        self.assert_about_panel_text(
            soup, expected_text, exclusivite_de_reprisereparation
        )
