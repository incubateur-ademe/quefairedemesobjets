import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestRobotsTxt:
    def test_infotri_configurator_is_disallowed(self, client):
        response = client.get("/robots.txt")
        assert response.status_code == 200
        infotri_url = reverse("infotri:configurator")
        assert f"Disallow: {infotri_url}" in response.text
