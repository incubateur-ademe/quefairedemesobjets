"""Tests for the BAN proxy view backing the carte address combobox."""

from unittest.mock import patch

import pytest
import requests
from django.urls import reverse


def _ban_response(*features):
    response = type("Response", (), {})()
    response.status_code = 200
    response.json = lambda: {"features": list(features)}
    response.raise_for_status = lambda: None
    return response


pytestmark = pytest.mark.django_db


@pytest.fixture
def url():
    return reverse("qfdmo:autocomplete_address")


def test_short_query_returns_only_geolocation_option(client, url):
    response = client.get(url, {"q": "ab", "turbo_frame_id": "test"})
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-geolocate="true"' in body
    assert "Autour de moi" in body
    assert body.count('role="option"') == 1


def test_query_returns_geolocation_option_then_features(client, url):
    fake_features = [
        {
            "properties": {"label": "12 Rue Test 75001 Paris", "context": "75, Paris"},
            "geometry": {"coordinates": [2.3522, 48.8566]},
        },
    ]
    with patch(
        "qfdmo.views.autocomplete.requests.get",
        return_value=_ban_response(*fake_features),
    ):
        response = client.get(url, {"q": "12 rue test", "turbo_frame_id": "test"})
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-geolocate="true"' in body
    assert "12 Rue Test 75001 Paris" in body
    assert 'data-lat="48.8566"' in body
    assert 'data-lon="2.3522"' in body


def test_network_failure_falls_back_to_geolocation_option(client, url):
    with patch(
        "qfdmo.views.autocomplete.requests.get",
        side_effect=requests.RequestException("boom"),
    ):
        response = client.get(url, {"q": "12 rue test", "turbo_frame_id": "test"})
    assert response.status_code == 200
    body = response.content.decode()
    assert "Autour de moi" in body
    assert body.count('role="option"') == 1


def test_response_carries_listbox_role(client, url):
    response = client.get(url, {"q": "", "turbo_frame_id": "test"})
    body = response.content.decode()
    assert 'role="listbox"' in body
    assert 'id="test-listbox"' in body


def test_response_is_publicly_cacheable(client, url):
    """Headers must let nginx/CDN cache shared BAN responses for 1h."""
    response = client.get(url, {"q": "", "turbo_frame_id": "test"})
    cache_control = response.headers.get("Cache-Control", "")
    assert "public" in cache_control
    assert "max-age=3600" in cache_control
