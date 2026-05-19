import logging
from typing import override

import requests
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control
from django.views.generic import ListView

logger = logging.getLogger(__name__)

BAN_API_URL = "https://data.geopf.fr/geocodage/search/"
BAN_REVERSE_API_URL = "https://data.geopf.fr/geocodage/reverse/"
BAN_TIMEOUT_SECONDS = 3

# Synthetic option always returned at the top of the listbox to let users
# trigger `navigator.geolocation` from the same combobox.
GEOLOCATE_OPTION = {
    "label": "Autour de moi",
    "sub_label": None,
    "latitude": None,
    "longitude": None,
    "geolocate": True,
}


@method_decorator(
    cache_control(public=True, max_age=60 * 60, stale_while_revalidate=60 * 5),
    name="dispatch",
)
class AutocompleteBanAddressView(ListView):
    """Server-rendered Turbo Frame listbox for the carte address combobox.

    Proxies the BAN (data.geopf.fr) geocoding search API and returns a list of
    `<li role="option">` entries. The first option is always the synthetic
    « Autour de moi » entry; the others come from BAN.

    Responses are public-cacheable for an hour so the proxy in front can serve
    repeated queries without round-tripping to BAN. Address reference data is
    shared across users and changes slowly.
    """

    template_name = "ui/forms/widgets/autocomplete/address_results.html"
    DEFAULT_LIMIT = 5
    MAX_LIMIT = 20
    MIN_QUERY_LENGTH = 3
    MAX_QUERY_LENGTH = 200

    @override
    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()[: self.MAX_QUERY_LENGTH]
        try:
            limit = int(self.request.GET.get("limit") or self.DEFAULT_LIMIT)
        except ValueError:
            limit = self.DEFAULT_LIMIT
        limit = max(1, min(limit, self.MAX_LIMIT))

        if len(query) < self.MIN_QUERY_LENGTH:
            return [GEOLOCATE_OPTION]

        try:
            response = requests.get(
                BAN_API_URL,
                params={"q": query},
                timeout=BAN_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json() or {}
            features = payload.get("features", []) or []
        except (requests.RequestException, ValueError) as exc:
            logger.warning("BAN proxy failed for query %r: %s", query, exc)
            return []

        options = []
        for feature in features[:limit]:
            try:
                options.append(
                    {
                        "label": feature["properties"]["label"],
                        "sub_label": feature["properties"].get("context"),
                        "latitude": feature["geometry"]["coordinates"][1],
                        "longitude": feature["geometry"]["coordinates"][0],
                        "geolocate": False,
                    }
                )
            except (KeyError, IndexError, TypeError):
                continue

        return options

    @override
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turbo_frame_id"] = self.request.GET.get("turbo_frame_id")
        context["results"] = self.object_list
        return context


@method_decorator(
    cache_control(public=True, max_age=60 * 60, stale_while_revalidate=60 * 5),
    name="dispatch",
)
class ReverseGeocodeBanView(View):
    """JSON proxy in front of BAN (data.geopf.fr) reverse-geocode.

    Mirrors `AutocompleteBanAddressView` so the browser never talks to BAN
    directly: avoids CORS / availability coupling and keeps a single
    server-side timeout + cache policy. Used by the carte address combobox
    when the user picks the synthetic "Autour de moi" geolocation option.

    Returns the matched BAN feature as JSON:

        {"adresse": "...", "latitude": <float>, "longitude": <float>}

    On no match or upstream failure returns 404 / 502 with an empty body so
    the client can surface a single user-facing error message.
    """

    def get(self, request, *args, **kwargs):
        try:
            lat = float(request.GET["lat"])
            lon = float(request.GET["lon"])
        except (KeyError, TypeError, ValueError):
            return HttpResponseBadRequest()

        # Guard against absurd values; BAN rejects them anyway but failing
        # fast avoids logging junk through the proxy.
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return HttpResponseBadRequest()

        try:
            response = requests.get(
                BAN_REVERSE_API_URL,
                params={"lat": lat, "lon": lon},
                timeout=BAN_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json() or {}
            features = payload.get("features", []) or []
        except (requests.RequestException, ValueError) as exc:
            logger.warning(
                "BAN reverse-geocode proxy failed for (%s, %s): %s", lat, lon, exc
            )
            return JsonResponse({}, status=502)

        if not features:
            return JsonResponse({}, status=404)

        try:
            feature = features[0]
            return JsonResponse(
                {
                    "adresse": feature["properties"]["label"],
                    "latitude": feature["geometry"]["coordinates"][1],
                    "longitude": feature["geometry"]["coordinates"][0],
                }
            )
        except (KeyError, IndexError, TypeError):
            return JsonResponse({}, status=502)
