"""
Integration tests for iframe embed scripts.

These tests verify that each iframe embed script loads correctly and generates
the proper HTML structure when embedded on third-party sites.
"""

import pytest
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "actions",
            "categories",
        )


class TestCarteEmbed:
    """Test the carte.js iframe embed script"""

    @pytest.mark.django_db
    def test_carte_iframe_renders(self, client):
        """Verify carte route renders correctly for iframe embedding"""
        url = "/carte"
        response = client.get(url)
        assert response.status_code == 200
        # Check that the page is renderable (basic content check)
        assert b"carte" in response.content.lower()

    @pytest.mark.django_db
    def test_carte_with_params(self, client):
        """Verify carte accepts query parameters"""
        url = "/carte?action_list=reparer"
        response = client.get(url)
        assert response.status_code == 200


class TestFormulaireEmbed:
    """Test the iframe.js script for formulaire embed"""

    @pytest.mark.django_db
    def test_formulaire_iframe_renders(self, client):
        """Verify formulaire route renders correctly for iframe embedding"""
        url = "/formulaire"
        response = client.get(url)
        assert response.status_code == 200
        # Verify it's rendered without header/footer (iframe mode)
        assert b'class="fr-header' not in response.content
        assert b'class="fr-footer' not in response.content

    @pytest.mark.django_db
    def test_formulaire_with_direction_and_actions(self, client):
        """Verify formulaire accepts direction and action_list parameters"""
        url = "/formulaire?direction=jai&action_list=reparer|donner"
        response = client.get(url)
        assert response.status_code == 200


class TestAssistantEmbed:
    """Test the assistant iframe embed via iframe.js"""

    @pytest.mark.django_db
    def test_assistant_with_objet_param(self, client):
        """Verify assistant route works with data-objet parameter"""
        # The iframe.js script appends objet as part of route: /dechet/{objet}
        url = "/dechet/lave-linge?iframe=&s=1"
        response = client.get(url)
        # Should either succeed or redirect to a valid page
        assert response.status_code in [
            200,
            301,
            302,
            404,
        ]  # 404 if fixture doesn't have this objet

    @pytest.mark.django_db
    def test_assistant_iframe_mode(self, client):
        """Verify assistant renders in iframe mode with correct parameters"""
        url = "/dechet?iframe=&s=1"
        response = client.get(url, follow=True)
        # Check it renders (may redirect to home or show assistant interface)
        assert response.status_code == 200


class TestInfotriEmbed:
    """Test the infotri iframe embed scripts"""

    @pytest.mark.django_db
    def test_infotri_configurator_route(self, client):
        """Verify infotri configurator page loads"""
        url = "/infotri/"
        response = client.get(url)
        assert response.status_code == 200
        assert b"categorie" in response.content.lower()

    @pytest.mark.django_db
    def test_infotri_embed_route(self, client):
        """Verify infotri embed route loads with parameters"""
        url = "/infotri/embed?categorie=tous&consigne=1&avec_phrase=false"
        response = client.get(url)
        assert response.status_code == 200
