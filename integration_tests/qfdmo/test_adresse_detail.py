import pytest
from bs4 import BeautifulSoup

from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory, LabelQualiteFactory


@pytest.mark.django_db
class TestDisplayLabel:
    def test_display_ess_label(self, client):
        adresse = DisplayedActeurFactory()
        label_ess = LabelQualiteFactory(
            code="ess",
            libelle="Enseigne de l'économie sociale et solidaire",
            type_enseigne=True,
        )
        adresse.labels.add(label_ess)

        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        label_tag = soup.find(attrs={"data-testid": "adresse_detail_header_tag"})
        assert label_tag is not None
        assert "Enseigne de l'économie sociale et solidaire" in label_tag.text

    def test_display_one_label(self, client):
        adresse = DisplayedActeurFactory()
        label = LabelQualiteFactory(
            code="label",
            libelle="Mon label",
        )
        adresse.labels.add(label)

        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        label_tag = soup.find(attrs={"data-testid": "adresse_detail_header_tag"})
        assert label_tag is not None
        assert "Mon label" in label_tag.text

    def test_display_two_label(self, client):
        adresse = DisplayedActeurFactory()
        label1 = LabelQualiteFactory(
            code="label1",
            libelle="Mon label 1",
        )
        label2 = LabelQualiteFactory(
            code="label2",
            libelle="Mon label 2",
        )
        adresse.labels.add(label1, label2)

        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        label_tag = soup.find(attrs={"data-testid": "adresse_detail_header_tag"})
        assert label_tag is not None
        assert "Cet établissement dispose de plusieurs labels" in label_tag.text

    def test_display_bonus_label(self, client):
        adresse = DisplayedActeurFactory()
        label = LabelQualiteFactory(
            code="label",
            libelle="Mon label",
            bonus=True,
        )
        adresse.labels.add(label)

        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        label_tag = soup.find(attrs={"data-testid": "adresse_detail_header_tag"})
        assert label_tag is not None
        assert "Éligible au bonus réparation" in label_tag.text

    def test_display_bonus_first_label(self, client):
        adresse = DisplayedActeurFactory()
        label_bonus = LabelQualiteFactory(
            code="label",
            libelle="Mon label",
            bonus=True,
        )
        label1 = LabelQualiteFactory(
            code="label1",
            libelle="Mon label 1",
        )
        label2 = LabelQualiteFactory(
            code="label2",
            libelle="Mon label 2",
        )
        label_ess = LabelQualiteFactory(
            code="ess",
            libelle="Enseigne de l'économie sociale et solidaire",
            type_enseigne=True,
        )
        adresse.labels.add(label_bonus, label1, label2, label_ess)

        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        label_tag = soup.find(attrs={"data-testid": "adresse_detail_header_tag"})
        assert label_tag is not None
        assert "Éligible au bonus réparation" in label_tag.text

    def test_display_label_before_ess(self, client):
        adresse = DisplayedActeurFactory()
        label = LabelQualiteFactory(
            code="label",
            libelle="Mon label",
        )
        label_ess = LabelQualiteFactory(
            code="ess",
            libelle="Enseigne de l'économie sociale et solidaire",
            type_enseigne=True,
        )
        adresse.labels.add(label, label_ess)

        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        label_tag = soup.find(attrs={"data-testid": "adresse_detail_header_tag"})
        assert label_tag is not None
        assert "Mon label" in label_tag.text


@pytest.mark.django_db
class TestUniquementSurRDV:
    def test_uniquement_sur_rdv_is_displayed(self, client):
        adresse = DisplayedActeurFactory(uniquement_sur_rdv=True)
        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        wrapper = soup.find(attrs={"id": "aboutPanel"})
        assert wrapper is not None
        assert (
            "Les services sont disponibles uniquement sur rendez-vous" in wrapper.text
        )
