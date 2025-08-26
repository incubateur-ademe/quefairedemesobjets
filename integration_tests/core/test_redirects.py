from urllib.parse import urlparse

import pytest
from django.conf import settings
from django.test import override_settings

host_aware_headers = {"Host": urlparse(settings.BASE_URL).hostname}


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "params,redirect_url",
    [
        ("?carte", "/carte"),
        ("?iframe", "/formulaire"),
        ("?iframe&direction=jai", "/formulaire?direction=jai"),
    ],
)
def test_redirect_with_carte_param(client, params, redirect_url):
    url = f"/{params}"
    redirect = client.get(url, headers=host_aware_headers)
    assert redirect.url == redirect_url
    response = client.get(redirect.url, headers=host_aware_headers)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "test_url",
    ["/configurateur", "/sitemap.xml", "/dsfr/colors"],
)
def test_other_routes_work(client, test_url):
    response = client.get(test_url, headers=host_aware_headers)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "test_url",
    [
        "/donnez-votre-avis",
        "/proposer-une-adresse",
        "/proposer-une-modification",
        "/nous-contacter",
    ],
)
def test_forms_redirects(client, test_url):
    response = client.get(test_url)
    assert response.status_code == 301


@pytest.mark.django_db
@override_settings(
    ALLOWED_HOSTS=[
        "quefairedemesdechets.ademe.fr",
        "lvao.ademe.fr",
        "quefairedemesobjets.ademe.fr",
    ],
    BASE_URL="https://quefairedemesdechets.ademe.fr",
)
@pytest.mark.parametrize(
    "host,url,expected_url,expected_status_code",
    [
        # Redirects to CMS
        ("lvao.ademe.fr", "", "https://quefairedemesdechets.ademe.fr/", 301),
        ("lvao.ademe.fr", "/", "https://quefairedemesdechets.ademe.fr/", 301),
        # Épargnons, Formulaire
        (
            "lvao.ademe.fr",
            "/formulaire",
            "https://quefairedemesdechets.ademe.fr/formulaire",
            301,
        ),
        # Carte
        ("lvao.ademe.fr", "/carte", "https://quefairedemesdechets.ademe.fr/carte", 301),
        # Scripts
        (
            "lvao.ademe.fr",
            "/static/iframe.js",
            "https://quefairedemesdechets.ademe.fr/static/iframe.js",
            301,
        ),
        (
            "lvao.ademe.fr",
            "/static/carte.js",
            "https://quefairedemesdechets.ademe.fr/static/carte.js",
            301,
        ),
        # Assistant
        ("quefairedemesdechets.ademe.fr", "/", None, 200),
        ("quefairedemesdechets.ademe.fr", "/carte", None, 200),
        (
            "quefairedemesdechets.ademe.fr",
            "/static/iframe.js",
            None,
            200,
        ),  # formulaire script
        (
            "quefairedemesdechets.ademe.fr",
            "/static/carte.js",
            None,
            200,
        ),  # carte script
        ("quefairedemesdechets.ademe.fr", "/iframe.js", None, 200),  # assistant script
    ],
)
def test_redirects(
    client,
    host,
    url,
    expected_url,
    expected_status_code,
):
    response = client.get(url, headers={"Host": host})
    assert response.status_code == expected_status_code
    if expected_url:
        assert response.url == expected_url
