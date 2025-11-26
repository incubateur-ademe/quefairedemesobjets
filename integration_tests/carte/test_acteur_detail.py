import json

import pytest
from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point

from qfdmo.models.acteur import ActeurStatus
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    LabelQualiteFactory,
    RevisionActeurFactory,
    SourceFactory,
)


@pytest.fixture
def get_response(client):
    def _get_response(uuid):
        url = f"/adresse_details/{uuid}"
        response = client.get(url)
        assert response.status_code == 200
        return response, BeautifulSoup(response.content, "html.parser")

    return _get_response


@pytest.mark.django_db
class TestDisplaySource:
    def test_display_no_source(self, get_response):
        adresse = DisplayedActeurFactory()
        response, _ = get_response(adresse.uuid)
        assert response.context["display_sources_panel"] is False

    def test_display_one_source(self, get_response):
        adresse = DisplayedActeurFactory()
        adresse.sources.add(SourceFactory(afficher=True))
        response, _ = get_response(adresse.uuid)
        assert response.context["display_sources_panel"] is True


@pytest.mark.django_db
class TestUTMSource:
    def test_utm_source_exists(self, get_response):
        adresse = DisplayedActeurFactory(nom="coucou", url="https://example.com")
        response, _ = get_response(adresse.uuid)
        assert "https://example.com?utm_source=quefairedemesobjets_ADEME" in str(
            response.content
        )

    def test_utm_source_does_not_exist_if_no_url(self, get_response):
        adresse = DisplayedActeurFactory(nom="coucou")
        response, _ = get_response(adresse.uuid)
        assert "utm_source=quefairedemesobjets_ADEME" not in str(response.content)


@pytest.mark.django_db
class TestDisplayNomCommercial:
    def test_nom_is_capitalized(self, get_response):
        adresse = DisplayedActeurFactory(nom="coucou", nom_commercial="")
        response, soup = get_response(adresse.uuid)
        acteur_title = soup.find(attrs={"data-testid": "acteur-title"})
        assert "Coucou" in acteur_title.text, "Test that the nom field is capitalized"

    def test_nom_commercial_is_displayed_if_present(self, get_response):
        adresse = DisplayedActeurFactory(nom="coucou", nom_commercial="youpi")
        response, soup = get_response(adresse.uuid)
        acteur_title = soup.find(attrs={"data-testid": "acteur-title"})
        assert "Youpi" in acteur_title.text, "Test that the nom commercial is displayed"


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
                "Propose le Bonus Réparation",
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

        response, soup = get_response(adresse.uuid)
        assert response.context["display_labels_panel"] == should_display
        # Labels are displayed in the header with data-testid="acteur-detail-labels"
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

        response, soup = get_response(adresse.uuid)
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

        response, soup = get_response(adresse.uuid)
        self.assert_about_panel_text(
            soup, expected_text, exclusivite_de_reprisereparation
        )


@pytest.mark.django_db
class TestRedirects:
    @pytest.mark.parametrize(
        "statut, expected_status_code",
        [
            (ActeurStatus.INACTIF, 301),
            (ActeurStatus.SUPPRIME, 301),
            (ActeurStatus.ACTIF, 200),
        ],
    )
    def test_acteur_status(self, client, statut, expected_status_code):
        acteur = DisplayedActeurFactory(
            identifiant_unique="coucou",
            statut=statut,
        )
        url = f"/adresse_details/{acteur.uuid}"
        response = client.get(url)
        assert response.status_code == expected_status_code

    def test_acteur_detail_redirect(self, client):
        acteur = DisplayedActeurFactory(
            identifiant_unique="coucou",
        )
        url = f"/adresse/{acteur.identifiant_unique}"
        response = client.get(url)
        assert response.status_code == 301

    def test_redirect_to_parent_acteur(self, client):
        parent_revision_acteur = RevisionActeurFactory(
            identifiant_unique="parent",
        )
        child_revision_acteur = RevisionActeurFactory(
            identifiant_unique="child",
            parent=parent_revision_acteur,
        )
        parent_displayed_acteur = DisplayedActeurFactory(
            identifiant_unique=parent_revision_acteur.identifiant_unique,
        )

        url = f"/adresse/{child_revision_acteur.identifiant_unique}"
        response = client.get(url)
        assert response.status_code == 301
        assert response.url == f"/adresse_details/{parent_displayed_acteur.uuid}"

    def test_adresse_details_404_not_found(self, client):
        url = "/adresse_details/doesnt_exist"
        response = client.get(url)
        assert response.status_code == 404

    def test_adresse_404_not_found(self, client):
        url = "/adresse/doesnt_exist"
        response = client.get(url)
        assert response.status_code == 404

    def not_found_actor_do_not_raise_error(self, client):
        pass


@pytest.mark.django_db
class TestSEO:
    @pytest.fixture
    def adresse(self):
        adresse = DisplayedActeurFactory(
            adresse="1 rue Johnny Haliday",
            ville="Groland",
            code_postal="12345",
            location=Point(1, 2),
        )
        return adresse

    def test_has_h1(self, get_response, adresse):
        response, soup = get_response(adresse.uuid)
        all_h1_tags = soup.find_all("h1")
        assert len(all_h1_tags) == 1, "Adresse detail page contains only one h1"
        assert (
            all_h1_tags[0].text.lower() == adresse.libelle.lower()
        ), "H1 contains adresse libelle"

    def test_json_ld(self, get_response, adresse):
        response, soup = get_response(adresse.uuid)
        structured_data = [
            json.loads(x.string)
            for x in soup.find_all("script", type="application/ld+json")
        ]

        assert len(structured_data) == 1
        assert structured_data[0] == json.loads(adresse.json_ld)
        assert structured_data[0]["address"]["addressLocality"] == "Groland"
        assert structured_data[0]["address"]["streetAddress"] == "1 rue Johnny Haliday"
        assert structured_data[0]["address"]["postalCode"] == "12345"
        assert structured_data[0]["geo"]["latitude"] == 2.0
        assert structured_data[0]["geo"]["longitude"] == 1.0
