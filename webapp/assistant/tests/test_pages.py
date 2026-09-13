import pytest
from django.urls import reverse

from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory


@pytest.mark.django_db
class TestRoutes:
    def test_home_responds(self, client):
        assert client.get(reverse("assistant:home")).status_code == 200

    def test_solutions_responds(self, client):
        assert client.get(reverse("assistant:solutions")).status_code == 200

    def test_produit_responds(self, client):
        page = ProduitPageFactory(parent=None)
        assert (
            client.get(reverse("assistant:produit", args=[page.slug])).status_code
            == 200
        )

    def test_lieu_responds(self, client):
        acteur = DisplayedActeurFactory()
        assert (
            client.get(reverse("assistant:lieu", args=[acteur.uuid])).status_code == 200
        )

    def test_unknown_produit_returns_404(self, client):
        assert (
            client.get(reverse("assistant:produit", args=["inconnu"])).status_code
            == 404
        )


@pytest.mark.django_db
class TestLayout:
    def test_serves_full_document_without_turbo_header(self, client):
        reponse = client.get(reverse("assistant:home"))
        assert b"<!DOCTYPE html>" in reponse.content

    def test_serves_fragment_with_turbo_header(self, client):
        """Turbo n'extrait que le frame : rendre le layout serait du travail jeté."""
        reponse = client.get(
            reverse("assistant:home"), headers={"Turbo-Frame": "assistant-fiche"}
        )
        assert b"<!DOCTYPE html>" not in reponse.content

    def test_layout_carries_no_dsfr(self, client):
        """L'assistant a son propre design system (ADR 0001)."""
        contenu = client.get(reverse("assistant:home")).content.decode()
        assert "dsfr" not in contenu.lower()

    def test_layout_has_skiplink(self, client):
        """RGAA 12.7 — sans {% dsfr_skiplinks %}, le nôtre doit être là."""
        assert "qfa-skiplink" in client.get(reverse("assistant:home")).content.decode()

    def test_layout_is_not_indexed(self, client):
        """#3434 : pas de SEO pour un contenu embarqué en iframe."""
        assert "noindex" in client.get(reverse("assistant:home")).content.decode()
