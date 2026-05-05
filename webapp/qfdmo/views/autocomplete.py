import logging
from typing import override

import requests
import unidecode
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance
from django.db.models.functions import Length, Lower
from django.views.generic import ListView

from qfdmd.models import Synonyme

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


class AutocompleteBanAddressView(ListView):
    """Server-rendered Turbo Frame results for the carte address combobox.

    Proxies the BAN (geopf) geocoding API and returns a list of options
    matching the W3C APG combobox-autocomplete-list pattern.

    The first option is always a synthetic « Autour de moi » entry that
    triggers `navigator.geolocation.getCurrentPosition` on the client.
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


class AutocompleteFormulaireSynonymeView(ListView):
    """Server-rendered Turbo Frame results for the formulaire object combobox.

    Returns a list of synonymes with the matching first sous_categorie_objet id
    so the client can populate both the visible (libelle) and hidden (sc_id)
    inputs on commit.
    """

    template_name = "ui/forms/widgets/autocomplete/formulaire_synonyme_results.html"
    DEFAULT_LIMIT = 10
    MIN_QUERY_LENGTH = 1

    @override
    def get_queryset(self):
        query = (self.request.GET.get("q") or "").strip()
        try:
            limit = int(self.request.GET.get("limit") or self.DEFAULT_LIMIT)
        except ValueError:
            limit = self.DEFAULT_LIMIT
        only_reemploi = bool(self.request.GET.get("only_reemploi"))

        if len(query) < self.MIN_QUERY_LENGTH:
            return []

        normalised = unidecode.unidecode(query)
        synonymes = (
            Synonyme.objects.annotate(nom_unaccent=Unaccent(Lower("nom")))
            .prefetch_related("produit__sous_categories")
            .annotate(
                distance=TrigramWordDistance(normalised, "nom_unaccent"),
                length=Length("nom"),
            )
            .filter(produit__sous_categories__id__isnull=False)
            .order_by("distance", "length")
        )
        if only_reemploi:
            synonymes = synonymes.filter(
                produit__sous_categories__reemploi_possible=True
            )
        synonymes = synonymes.distinct()[:limit]

        results = []
        for synonyme in synonymes:
            sous_categorie = synonyme.produit.sous_categories.first()
            if sous_categorie is None:
                continue
            results.append(
                {
                    "label": synonyme.nom,
                    "sub_label": sous_categorie.libelle,
                    "sc_id": sous_categorie.id,
                }
            )
        return results

    @override
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turbo_frame_id"] = self.request.GET.get("turbo_frame_id")
        context["results"] = self.get_queryset()
        return context
