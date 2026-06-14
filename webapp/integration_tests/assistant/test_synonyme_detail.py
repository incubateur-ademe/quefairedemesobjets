# flake8: noqa: E501
import pytest
from bs4 import BeautifulSoup

from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory


@pytest.mark.django_db
class TestSynonyme:
    def test_canonical(self, client):
        produit = ProduitFactory(nom="Un super produit")
        synonyme = SynonymeFactory(produit=produit, nom="Un synonyme")
        response = client.get(
            synonyme.get_absolute_url(),
        )
        assert response.status_code == 200, "No redirect occurs"
        soup = BeautifulSoup(response.content, "html.parser")
        assert (
            f"""<link href="http://testserver/dechet/{synonyme.slug}/" rel="canonical"/>"""
            in str(soup)
        )

    def test_canonical_with_querystring(self, client):
        produit = ProduitFactory(nom="Un super produit")
        synonyme = SynonymeFactory(produit=produit, nom="Un synonyme")
        response = client.get(
            f"{synonyme.get_absolute_url()}?utm_source=une-source-utm",
        )
        assert response.status_code == 200, "No redirect occurs"
        soup = BeautifulSoup(response.content, "html.parser")
        assert (
            f"""<link href="http://testserver/dechet/{synonyme.slug}/" rel="canonical"/>"""
            in str(soup)
        )

    def test_footer_primary_button_points_at_standalone_fiche(self, client):
        produit = ProduitFactory(nom="Un super produit")
        synonyme = SynonymeFactory(produit=produit, nom="Un synonyme")

        response = client.get(synonyme.get_absolute_url())

        assert response.status_code == 200, "No redirect occurs"
        button = response.context["footer_primary_button"]
        assert button["label"] == "Lire plus sur cette fiche"
        assert synonyme.get_absolute_url() in button["onclick"]
        assert "utm_source=qfdmod" in button["onclick"]
        assert "_blank" in button["onclick"]
