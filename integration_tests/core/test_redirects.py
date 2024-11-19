import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_redirect_without_param(client):
    url = "/"
    response = client.get(url)
    assert response.status_code == 301
    assert response.url == "https://longuevieauxobjets.ademe.fr"


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
    redirect = client.get(url)
    assert redirect.url == redirect_url
    response = client.get(redirect.url)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "test_url",
    ["/configurateur", "/sitemap.xml", "/dsfr/colors", "/connexion"],
)
def test_other_routes_work(client, test_url):
    response = client.get(test_url)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "test_url",
    [
        "/dags/validations",
        "/iframe/configurateur",
    ],
)
def test_protected_routes_works(client, test_url):
    response = client.get(test_url)
    assert response.status_code == 302
    assert response.url.startswith("/connexion")


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
def test_redirects(client, test_url):
    response = client.get(test_url)
    assert response.status_code == 301
