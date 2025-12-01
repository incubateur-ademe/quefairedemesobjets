"""
Integration tests for iframe embed scripts.

These tests verify that all embed script routes return 200 status code.
For iframe ID validation tests, see e2e_tests/lookbook_iframes.spec.ts
"""

import pytest


class TestEmbedScriptRoutes:
    """Test that all embed script routes are accessible"""

    @pytest.mark.django_db
    def test_carte_script_loads(self, client):
        """Verify carte.js script is accessible"""
        response = client.get("/static/carte.js")
        assert response.status_code == 200
        assert response["Content-Type"] in [
            "application/javascript",
            "text/javascript",
        ]

    @pytest.mark.django_db
    def test_iframe_script_loads(self, client):
        """Verify iframe.js script is accessible (used by formulaire and assistant)"""
        response = client.get("/static/iframe.js")
        assert response.status_code == 200
        assert response["Content-Type"] in [
            "application/javascript",
            "text/javascript",
        ]

    @pytest.mark.django_db
    def test_infotri_script_loads(self, client):
        """Verify infotri.js embed script is accessible"""
        response = client.get("/infotri/static/infotri.js")
        assert response.status_code == 200
        assert response["Content-Type"] in [
            "application/javascript",
            "text/javascript",
        ]

    @pytest.mark.django_db
    def test_infotri_configurator_script_loads(self, client):
        """Verify infotri-configurator.js embed script is accessible"""
        response = client.get("/infotri/static/infotri-configurator.js")
        assert response.status_code == 200
        assert response["Content-Type"] in [
            "application/javascript",
            "text/javascript",
        ]
