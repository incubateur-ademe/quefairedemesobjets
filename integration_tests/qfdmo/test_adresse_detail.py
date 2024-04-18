import pytest
from bs4 import BeautifulSoup

from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory, LabelQualiteFactory


@pytest.mark.django_db
class TestDisplayLabel:
    def test_display_ess_label(self, client):

        adresse = DisplayedActeurFactory()
        label = LabelQualiteFactory(
            code="ess",
            libelle="Enseigne de l'économie sociale et solidaire",
            type_enseigne=True,
        )
        adresse.labels.add(label)

        url = f"/adresse/{adresse.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        label_tag = soup.find("p", {"class": "fr-tag"})
        assert label_tag is not None
        assert "Enseigne de l'économie sociale et solidaire" in label_tag.text
