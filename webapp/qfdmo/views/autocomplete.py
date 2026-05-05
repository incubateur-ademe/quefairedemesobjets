import logging
from typing import override

import requests
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.generic import ListView

logger = logging.getLogger(__name__)

BAN_API_URL = "https://data.geopf.fr/geocodage/search/?q={}"
BAN_TIMEOUT_SECONDS = 3
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
    """Server-rendered Turbo Frame results for the carte address combobox.

    Proxies the BAN (geopf) geocoding API and returns a list of options
    matching the W3C APG combobox-autocomplete-list pattern.

    The first option is always a synthetic « Autour de moi » entry that
    triggers `navigator.geolocation.getCurrentPosition` on the client.

    Responses are public-cacheable for 1 hour so nginx (and any CDN /
    intermediate cache) can serve repeated queries without hitting BAN.
    Address reference data is shared across users and changes slowly.
    """

    template_name = "ui/forms/widgets/autocomplete/address_results.html"
    DEFAULT_LIMIT = 5
    MIN_QUERY_LENGTH = 3

    @override
    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        try:
            limit = int(self.request.GET.get("limit") or self.DEFAULT_LIMIT)
        except ValueError:
            limit = self.DEFAULT_LIMIT

        if len(query) < self.MIN_QUERY_LENGTH:
            return [GEOLOCATE_OPTION]

        try:
            response = requests.get(
                BAN_API_URL.format(query),
                timeout=BAN_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            features = response.json().get("features", [])
        except (requests.RequestException, ValueError) as exc:
            logger.warning("BAN proxy failed for query %r: %s", query, exc)
            return [GEOLOCATE_OPTION]

        options = [
            {
                "label": feature["properties"]["label"],
                "sub_label": feature["properties"].get("context"),
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0],
                "geolocate": False,
            }
            for feature in features[:limit]
        ]
        return [GEOLOCATE_OPTION] + options

    @override
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turbo_frame_id"] = self.request.GET.get("turbo_frame_id")
        context["results"] = self.get_queryset()
        return context
