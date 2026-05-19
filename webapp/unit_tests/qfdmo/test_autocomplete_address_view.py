"""Unit tests for AutocompleteBanAddressView (the carte BAN proxy).

Covers the boundary cases that aren't easy to exercise in e2e:

  - short / oversized / blank queries
  - `limit` parameter clamping
  - BAN returning a non-JSON or malformed response
  - one malformed feature shouldn't poison the rest
  - the synthetic "Autour de moi" geolocate option

Network calls to data.geopf.fr are mocked with `responses`.
"""

import json
from unittest.mock import patch

import pytest
import requests
from django.test import RequestFactory
from django.urls import reverse

from qfdmo.views.autocomplete import (
    BAN_API_URL,
    BAN_REVERSE_API_URL,
    GEOLOCATE_OPTION,
    AutocompleteBanAddressView,
    ReverseGeocodeBanView,
)


def _view_response(request):
    """Invoke the class-based view and return the rendered HttpResponse.

    ListView returns a TemplateResponse which is lazy. We call `.render()`
    so `.content` is available to assertions.
    """
    response = AutocompleteBanAddressView.as_view()(request)
    response.render()
    return response


def _make_request(**get_params):
    factory = RequestFactory()
    return factory.get(reverse("qfdmo:autocomplete_address"), data=get_params)


@pytest.mark.django_db
class TestAutocompleteBanAddressViewQueryHandling:
    """Behavior driven by the GET parameters before any BAN call."""

    def test_short_query_returns_only_geolocate_option(self):
        response = _view_response(_make_request(q="ab", turbo_frame_id="frame-1"))
        assert response.status_code == 200
        assert b"Autour de moi" in response.content
        assert b'data-geolocate="true"' in response.content

    def test_blank_query_returns_only_geolocate_option(self):
        response = _view_response(_make_request(q="", turbo_frame_id="frame-1"))
        assert b"Autour de moi" in response.content

    def test_missing_query_returns_only_geolocate_option(self):
        response = _view_response(_make_request(turbo_frame_id="frame-1"))
        assert b"Autour de moi" in response.content

    def test_oversized_query_is_truncated_before_calling_ban(self):
        long_q = "x" * (AutocompleteBanAddressView.MAX_QUERY_LENGTH + 50)
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.json.return_value = {"features": []}
            ban.return_value.raise_for_status.return_value = None
            _view_response(_make_request(q=long_q, turbo_frame_id="f"))
        sent_q = ban.call_args.kwargs["params"]["q"]
        assert len(sent_q) == AutocompleteBanAddressView.MAX_QUERY_LENGTH


@pytest.mark.django_db
class TestAutocompleteBanAddressViewLimitClamping:
    """The `limit` parameter must fall back / clamp safely."""

    @pytest.mark.parametrize(
        "limit_param,expected_capped",
        [
            ("3", 3),
            ("0", 1),
            ("-5", 1),
            ("9999", AutocompleteBanAddressView.MAX_LIMIT),
            ("not-a-number", AutocompleteBanAddressView.DEFAULT_LIMIT),
            (None, AutocompleteBanAddressView.DEFAULT_LIMIT),
        ],
    )
    def test_limit_is_clamped_to_safe_bounds(self, limit_param, expected_capped):
        features = [
            {
                "properties": {"label": f"Result {i}", "context": "ctx"},
                "geometry": {"coordinates": [1.0 + i, 2.0 + i]},
            }
            for i in range(50)
        ]
        params = {"q": "Paris", "turbo_frame_id": "frame"}
        if limit_param is not None:
            params["limit"] = limit_param

        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.json.return_value = {"features": features}
            ban.return_value.raise_for_status.return_value = None
            response = _view_response(_make_request(**params))

        assert response.status_code == 200
        rendered_count = response.content.count(b'role="option"')
        assert rendered_count == expected_capped


@pytest.mark.django_db
class TestAutocompleteBanAddressViewBanResilience:
    """Network and parsing failures must degrade gracefully."""

    def test_ban_timeout_returns_empty_listbox(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.side_effect = requests.Timeout("BAN slow")
            response = _view_response(_make_request(q="Paris", turbo_frame_id="frame"))
        assert response.status_code == 200
        # "Aucune adresse trouvée" is the empty-state message
        assert b"Aucune adresse trouv" in response.content

    def test_ban_returns_invalid_json(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.side_effect = ValueError("not json")
            response = _view_response(_make_request(q="Paris", turbo_frame_id="frame"))
        assert response.status_code == 200
        assert b"Aucune adresse trouv" in response.content

    def test_one_malformed_feature_is_skipped(self):
        good = {
            "properties": {"label": "Auray", "context": "56, Morbihan"},
            "geometry": {"coordinates": [-2.99, 47.66]},
        }
        malformed = {"properties": {}, "geometry": {}}
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = {"features": [malformed, good]}
            response = _view_response(_make_request(q="Auray", turbo_frame_id="frame"))
        body = response.content.decode()
        # The good entry rendered, the malformed one was silently dropped.
        assert "Auray" in body
        assert body.count('role="option"') == 1

    def test_ban_returns_null_features(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = {"features": None}
            response = _view_response(_make_request(q="Paris", turbo_frame_id="frame"))
        assert response.status_code == 200
        assert b"Aucune adresse trouv" in response.content


@pytest.mark.django_db
class TestAutocompleteBanAddressViewRendering:
    """The Turbo Frame contract: id matches the query param, lat/lon are
    unlocalized (`.` separator), structure carries ARIA roles."""

    def _ban_returns_one_result(self):
        return {
            "features": [
                {
                    "properties": {
                        "label": "Auray",
                        "context": "56, Morbihan, Bretagne",
                    },
                    "geometry": {"coordinates": [-2.990838, 47.668099]},
                }
            ]
        }

    def test_turbo_frame_id_echoes_the_request_param(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = self._ban_returns_one_result()
            response = _view_response(
                _make_request(q="Auray", turbo_frame_id="some-uuid-here")
            )
        assert b'id="some-uuid-here"' in response.content
        assert b'id="some-uuid-here-listbox"' in response.content

    def test_listbox_role_is_present(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = self._ban_returns_one_result()
            response = _view_response(_make_request(q="Auray", turbo_frame_id="frame"))
        assert b'role="listbox"' in response.content
        assert b'role="option"' in response.content

    def test_lat_lon_are_unlocalized(self):
        # Coordinates must use `.` decimal separator regardless of LOCALE so
        # the JS dataset can parseFloat them.
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = self._ban_returns_one_result()
            response = _view_response(_make_request(q="Auray", turbo_frame_id="frame"))
        body = response.content.decode()
        assert 'data-lat="47.668099"' in body
        assert 'data-lon="-2.990838"' in body
        # Belt-and-suspenders: no French decimal slipped through.
        assert "47,668099" not in body

    def test_sub_label_is_rendered_when_present(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = self._ban_returns_one_result()
            response = _view_response(_make_request(q="Auray", turbo_frame_id="frame"))
        assert b"56, Morbihan, Bretagne" in response.content


@pytest.mark.django_db
class TestAutocompleteBanAddressViewBanRequest:
    """The view must hit BAN with the expected URL and a short timeout."""

    def test_request_targets_data_geopf_with_query(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = {"features": []}
            _view_response(_make_request(q="Paris", turbo_frame_id="frame"))
        assert ban.call_args.args[0] == BAN_API_URL
        assert ban.call_args.kwargs["params"] == {"q": "Paris"}
        # Hardcoded 3s timeout — guards against the carte hanging on slow BAN.
        assert ban.call_args.kwargs["timeout"] == 3


class TestGeolocateOption:
    """Smoke check on the constant — it's referenced from results templates,
    so a typo would silently disable the « Autour de moi » entry."""

    def test_geolocate_option_carries_required_keys(self):
        assert GEOLOCATE_OPTION["geolocate"] is True
        assert GEOLOCATE_OPTION["label"] == "Autour de moi"
        # Coordinates are intentionally None: the client uses
        # `navigator.geolocation` instead of any baked-in lat/lon.
        assert GEOLOCATE_OPTION["latitude"] is None
        assert GEOLOCATE_OPTION["longitude"] is None


def _reverse_request(**get_params):
    factory = RequestFactory()
    return factory.get(reverse("qfdmo:reverse_geocode_address"), data=get_params)


@pytest.mark.django_db
class TestReverseGeocodeBanView:
    """JSON proxy in front of BAN reverse-geocode (Autour de moi → adresse)."""

    def _ban_returns_one_match(self):
        return {
            "features": [
                {
                    "properties": {"label": "10 Rue de Paris, 56400 Auray"},
                    "geometry": {"coordinates": [-2.990838, 47.668099]},
                }
            ]
        }

    def test_returns_label_and_swapped_coordinates(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = self._ban_returns_one_match()
            response = ReverseGeocodeBanView.as_view()(
                _reverse_request(lat="47.668099", lon="-2.990838")
            )
        assert response.status_code == 200
        assert json.loads(response.content) == {
            "adresse": "10 Rue de Paris, 56400 Auray",
            "latitude": 47.668099,
            "longitude": -2.990838,
        }

    def test_targets_ban_reverse_endpoint_with_parsed_floats(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = self._ban_returns_one_match()
            ReverseGeocodeBanView.as_view()(
                _reverse_request(lat="47.668099", lon="-2.990838")
            )
        assert ban.call_args.args[0] == BAN_REVERSE_API_URL
        # Parsed as floats — protects against query-string passthrough.
        assert ban.call_args.kwargs["params"] == {
            "lat": 47.668099,
            "lon": -2.990838,
        }
        assert ban.call_args.kwargs["timeout"] == 3

    @pytest.mark.parametrize(
        "params",
        [
            {},
            {"lat": "47.6"},
            {"lon": "2.3"},
            {"lat": "not-a-number", "lon": "2.3"},
            {"lat": "47.6", "lon": "abc"},
        ],
    )
    def test_missing_or_malformed_params_return_400(self, params):
        response = ReverseGeocodeBanView.as_view()(_reverse_request(**params))
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "params",
        [
            {"lat": "91", "lon": "2.3"},
            {"lat": "-91", "lon": "2.3"},
            {"lat": "47", "lon": "181"},
            {"lat": "47", "lon": "-181"},
        ],
    )
    def test_out_of_range_params_return_400(self, params):
        response = ReverseGeocodeBanView.as_view()(_reverse_request(**params))
        assert response.status_code == 400

    def test_ban_timeout_returns_502(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.side_effect = requests.Timeout("BAN slow")
            response = ReverseGeocodeBanView.as_view()(
                _reverse_request(lat="47.6", lon="2.3")
            )
        assert response.status_code == 502

    def test_empty_features_returns_404(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = {"features": []}
            response = ReverseGeocodeBanView.as_view()(
                _reverse_request(lat="47.6", lon="2.3")
            )
        assert response.status_code == 404

    def test_malformed_feature_returns_502(self):
        with patch("qfdmo.views.autocomplete.requests.get") as ban:
            ban.return_value.raise_for_status.return_value = None
            ban.return_value.json.return_value = {"features": [{"properties": {}}]}
            response = ReverseGeocodeBanView.as_view()(
                _reverse_request(lat="47.6", lon="2.3")
            )
        assert response.status_code == 502
