from urllib.parse import urlencode

import pytest
from bs4 import BeautifulSoup

from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


@pytest.fixture
def get_carte_config_response_and_soup(client):
    def _get_carte_config_from(slug, params={}):
        url = f"/carte/{slug}/?{urlencode(params)}"
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

    def test_legend_is_visible_by_default(self, get_carte_config_response_and_soup):
        carte_config = CarteConfigFactory()  # hide_legend is False by default
        params = {"adresse": "Paris", "longitude": "2.347", "latitude": "48.859"}
        response, soup = get_carte_config_response_and_soup(
            carte_config.slug,
            params,
        )
        assert soup.find(attrs={"data-testid": "legend-mobile-button"}) is not None
        assert soup.find(attrs={"data-testid": "carte-legend"}) is not None
        assert soup.find(attrs={"data-testid": "carte-legend-mobile"}) is not None

    def test_legend_can_be_hidden(self, get_carte_config_response_and_soup):
        params = {"adresse": "Paris", "longitude": "2.347", "latitude": "48.859"}
        carte_config = CarteConfigFactory(hide_legend=True)
        response, soup = get_carte_config_response_and_soup(
            carte_config.slug,
            params,
        )
        assert soup.find(attrs={"data-testid": "legend-mobile-button"}) is None
        assert soup.find(attrs={"data-testid": "carte-legend"}) is None
        assert soup.find(attrs={"data-testid": "carte-legend-mobile"}) is None
