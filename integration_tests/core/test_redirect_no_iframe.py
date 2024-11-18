import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_redirect_without_param(client):
    url = "/"
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_redirect_with_carte_param(client):
    url = "/?carte"
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_redirect_with_iframe_param(client):
    url = "/?iframe"
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_no_redirect_configurateur(client):
    url = "/configurateur"
    response = client.get(url)

    assert response.status_code == 200
