from urllib.parse import urlencode

import pytest
from bs4 import BeautifulSoup
from django.core.management import call_command

from qfdmo.models.action import GroupeAction
from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "categories",
            "actions",
            "acteur_services",
            "acteur_types",
            "produits",
            "synonymes",
        )


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
    @pytest.fixture
    def params(self):
        return {"adresse": "Paris", "longitude": "2.347", "latitude": "48.859"}

    def test_carte_config_context_name(
        self, get_carte_config_response_and_soup, params
    ):
        carte_config = CarteConfigFactory(cacher_legende=True)
        response, _ = get_carte_config_response_and_soup(carte_config.slug)
        assert "carte_config" in response.context

    def test_legacy_query_string_keep_working(
        self, get_carte_config_response_and_soup, params
    ):
        carte_config = CarteConfigFactory()  # cacher_legende is False by default
        code = "preter"
        params.update(action_displayed=code, action_list=code)
        params.update(longitude=-2.990838, latitude=47.668099)
        response, soup = get_carte_config_response_and_soup(
            carte_config.slug,
            params,
        )
        assert response.context["forms"]["legende"]["groupe_action"].value() == list(
            GroupeAction.objects.filter(
                actions__code__in=[code], afficher=True
            ).values_list("id", flat=True)
        )

    def test_legend_can_be_hidden(self, get_carte_config_response_and_soup, params):
        carte_config = CarteConfigFactory(cacher_legende=True)
        response, soup = get_carte_config_response_and_soup(
            carte_config.slug,
            params,
        )
        assert soup.find(attrs={"data-testid": "legend-mobile-button"}) is None
        assert soup.find(attrs={"data-testid": "carte-legend"}) is None
        assert soup.find(attrs={"data-testid": "carte-legend-mobile"}) is None

    def test_preview_screen(self, get_carte_config_response_and_soup):
        carte_config = CarteConfigFactory(
            titre_previsualisation="Youpi",
            contenu_previsualisation="Coucou",
        )
        response, soup = get_carte_config_response_and_soup(
            carte_config.slug,
        )
        assert soup.find(attrs={"data-testid": "preview-title"}).text.strip() == "Youpi"
        assert (
            soup.find(attrs={"data-testid": "preview-content"}).text.strip() == "Coucou"
        )

    def test_cyclevia_regresion(self, get_carte_config_response_and_soup):
        """A regression introduced by adding the CarteConfig as a wagtail block
        caused the Cyclevia CarteConfig to fail after a search, because it does
        not use any sous_categorie_objet.
        This test ensures that the regression is fixed."""
        carte_config_without_sous_categories = CarteConfigFactory()
        response, soup = get_carte_config_response_and_soup(
            carte_config_without_sous_categories.slug,
            {
                "adresse": "Auray",
                "longitude": "-2.990838",
                "latitude": "47.668099",
                "carte": "",
                "r": "55",
                "bounding_box": "",
                "direction": "",
                "action_displayed": "trier",
                "sous_categorie_objet": "",
                "sc_id": "",
            },
        )
        assert response.status_code == 200
