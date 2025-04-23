import pytest
from bs4 import BeautifulSoup

from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


@pytest.fixture
def get_carte_config_response_and_soup(client):
    def _get_carte_config_from(slug):
        url = f"/carte/{slug}/"
        response = client.get(url)
        assert response.status_code == 200
        return response, BeautifulSoup(response.content, "html.parser")

    return _get_carte_config_from


@pytest.mark.django_db
class TestCarteConfig:
    def test_carte_config_context_name(self, get_carte_config_response_and_soup):
        carte_config = CarteConfigFactory(hide_legend=True)
        response, _ = get_carte_config_response_and_soup(carte_config.slug)
        assert "carte_config" in response.context

    def test_legend_can_be_hidden(self, get_carte_config_response_and_soup):
        carte_config = CarteConfigFactory(hide_legend=True)
        response, _ = get_carte_config_response_and_soup(carte_config.slug)
