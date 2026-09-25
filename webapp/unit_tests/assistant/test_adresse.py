from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

# The test settings use DummyCache, which remembers nothing: the two tests
# about the cache need a real backend to say anything.
IN_MEMORY_CACHE = override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-adresse",
        }
    }
)

pytestmark = pytest.mark.django_db


def ban_response(*features):
    """Mimics the BAN response, of which only the shape matters here."""

    class Fake:
        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"features": list(features)}

    return Fake()


def feature(label, ban_type, longitude=2.35, latitude=48.85, context="75, Paris"):
    return {
        "properties": {"label": label, "type": ban_type, "context": context},
        "geometry": {"coordinates": [longitude, latitude]},
    }


@pytest.fixture(autouse=True)
def empty_cache():
    cache.clear()
    yield
    cache.clear()


class TestAdresseSearch:
    def test_too_short_query_does_not_reach_the_ban(self, client):
        with patch("assistant.adresses.requests.get") as request:
            response = client.get(reverse("api_v1:adresses"), {"q": "ab"})

        assert response.json() == {"results": []}
        request.assert_not_called()

    def test_precise_address(self, client):
        with patch(
            "assistant.adresses.requests.get",
            return_value=ban_response(
                feature("8 Rue de Rivoli 75004 Paris", "housenumber")
            ),
        ):
            results = client.get(
                reverse("api_v1:adresses"), {"q": "8 rue de rivoli"}
            ).json()["results"]

        assert results == [
            {
                "label": "8 Rue de Rivoli 75004 Paris",
                "detail": "75, Paris",
                "longitude": 2.35,
                "latitude": 48.85,
                "precise": True,
            }
        ]

    @pytest.mark.parametrize(
        "ban_type,precise",
        [
            ("housenumber", True),
            ("street", True),
            ("locality", True),
            ("municipality", False),
        ],
    )
    def test_only_a_municipality_is_not_precise(self, client, ban_type, precise):
        """The red marker only shows for a precise point (#3356)."""
        with patch(
            "assistant.adresses.requests.get",
            return_value=ban_response(feature("Lyon", ban_type)),
        ):
            results = client.get(reverse("api_v1:adresses"), {"q": "lyon"}).json()[
                "results"
            ]

        assert results[0]["precise"] is precise

    def test_ban_outage_yields_an_empty_list(self, client):
        import requests

        with patch(
            "assistant.adresses.requests.get",
            side_effect=requests.RequestException("unreachable"),
        ):
            response = client.get(reverse("api_v1:adresses"), {"q": "paris"})

        assert response.status_code == 200
        assert response.json() == {"results": []}

    @IN_MEMORY_CACHE
    def test_an_outage_is_not_cached(self, client):
        """Otherwise a passing outage would freeze for 24 h."""
        import requests

        with patch(
            "assistant.adresses.requests.get",
            side_effect=requests.RequestException("unreachable"),
        ):
            client.get(reverse("api_v1:adresses"), {"q": "paris"})

        with patch(
            "assistant.adresses.requests.get",
            return_value=ban_response(feature("Paris", "municipality")),
        ) as request:
            results = client.get(reverse("api_v1:adresses"), {"q": "paris"}).json()[
                "results"
            ]

        request.assert_called_once()
        assert results[0]["label"] == "Paris"

    @IN_MEMORY_CACHE
    def test_the_cache_avoids_a_second_call(self, client):
        with patch(
            "assistant.adresses.requests.get",
            return_value=ban_response(feature("Auray", "municipality")),
        ) as request:
            client.get(reverse("api_v1:adresses"), {"q": "auray"})
            client.get(reverse("api_v1:adresses"), {"q": "AURAY"})

        request.assert_called_once()

    def test_unusable_feature_is_ignored(self, client):
        """The BAN may return a feature without label or without coordinates."""
        with patch(
            "assistant.adresses.requests.get",
            return_value=ban_response(
                {"properties": {"type": "street"}, "geometry": {}},
                feature("Auray", "municipality"),
            ),
        ):
            results = client.get(reverse("api_v1:adresses"), {"q": "auray"}).json()[
                "results"
            ]

        assert [r["label"] for r in results] == ["Auray"]
