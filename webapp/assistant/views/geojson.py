import math
from time import perf_counter

from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control

from qfdmd.models import ProduitPage
from qfdmo.map_utils import sanitize_frontend_bbox
from qfdmo.models.acteur import MAX_PLACES_ON_MAP, DisplayedActeur


class InvalidPosition(ValueError):
    pass


def sous_categorie_ids_for(slug: str) -> list[int]:
    """Sous-catégories of the fiche, to narrow the places to that objet.

    A fiche without sous-catégorie returns an empty list: the places are then
    not narrowed, rather than showing none.
    """
    page = ProduitPage.objects.live().filter(slug=slug).first()
    if page is None:
        raise Http404(f"unknown objet: {slug}")
    return list(page.sous_categorie_objet.values_list("id", flat=True))


def coordinate(query, name: str, bound: float) -> float:
    value = float(query[name])
    if not math.isfinite(value) or abs(value) > bound:
        raise ValueError(name)
    return value


def position_from(query) -> dict:
    """Reads the requested position, giving priority to the visible area.

    An unreadable bbox is refused rather than falling back on lat/lon: the
    fallback would hide a client bug and show an area the user is not looking
    at.
    """
    if raw_bbox := query.get("bbox"):
        bbox = sanitize_frontend_bbox(raw_bbox)
        if not bbox:
            raise InvalidPosition("bbox")
        return {"bbox": bbox, "longitude": None, "latitude": None}

    try:
        return {
            "bbox": None,
            "longitude": coordinate(query, "lon", 180),
            "latitude": coordinate(query, "lat", 90),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidPosition("lat/lon") from error


@method_decorator(
    cache_control(public=True, max_age=300, stale_while_revalidate=60),
    name="dispatch",
)
class LieuxGeoJSONView(View):
    def get(self, request, *args, **kwargs):
        geste = request.GET.get("geste")
        if not geste:
            return HttpResponseBadRequest("missing geste")

        try:
            position = position_from(request.GET)
        except InvalidPosition as error:
            return HttpResponseBadRequest(f"invalid position: {error}")

        sous_categorie_ids = (
            sous_categorie_ids_for(objet) if (objet := request.GET.get("objet")) else []
        )

        acteurs = DisplayedActeur.objects.all().proposing(geste, sous_categorie_ids)
        if position["bbox"]:
            acteurs = acteurs.within(position["bbox"])
        else:
            acteurs = acteurs.nearest_to(position["longitude"], position["latitude"])

        start = perf_counter()
        payload = acteurs.for_the_map(MAX_PLACES_ON_MAP).as_geojson()
        duration_ms = (perf_counter() - start) * 1000

        response = JsonResponse(payload)
        # Read by the browser (Network tab, PerformanceObserver) and by the
        # map's debug overlay.
        timing = f'acteurs;dur={duration_ms:.1f};desc="lieux"'
        response.headers["Server-Timing"] = timing
        return response
