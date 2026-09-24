from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control

from assistant.parcours import Parcours
from assistant.views.geojson import sous_categorie_ids_for
from qfdmo.models.acteur import DisplayedActeur

# "À proximité": the 20 km the spec mentions as the map's maximum radius (#3356).
RADIUS_KM = 20
COUNT_CACHE_TTL = 60 * 60 * 12
# Two decimals: about a kilometre. The counter is approximate by design
# (ADR 0010): neighbours a street apart share one entry.
COORDINATE_PRECISION = 2


@method_decorator(
    cache_control(public=True, max_age=300, stale_while_revalidate=60),
    name="dispatch",
)
class SolutionsCountView(View):
    """Number of places offering the gestes of a block near the address.

    Fetched by the fiche *after* it renders: counting costs up to half a
    second on a large objet (ADR 0010), far beyond the page's budget, so the
    page never waits for it. The result is cached 12 h per gestes, objet and
    ~1 km cell, the same lifetime as the offers cache: the data only moves
    with the imports.
    """

    def get(self, request, *args, **kwargs):
        gestes = [g.strip() for g in request.GET.getlist("geste") if g.strip()]
        parcours = Parcours.from_query(request.GET)
        if not gestes or not parcours.is_located:
            return HttpResponseBadRequest("geste and position required")

        slug = (request.GET.get("fiche") or "").strip()
        try:
            sous_categorie_ids = sous_categorie_ids_for(slug) if slug else []
        except Http404:
            return HttpResponseBadRequest(f"unknown objet: {slug}")

        cell = (
            round(parcours.longitude, COORDINATE_PRECISION),
            round(parcours.latitude, COORDINATE_PRECISION),
        )
        key = "compte:{}:{}:{}:{}".format(
            ",".join(sorted(gestes)),
            ",".join(map(str, sorted(sous_categorie_ids))),
            cell[0],
            cell[1],
        )
        count = cache.get(key)
        if count is None:
            count = _count(gestes, sous_categorie_ids, cell)
            cache.set(key, count, COUNT_CACHE_TTL)
        return JsonResponse({"count": count})


def _count(gestes, sous_categorie_ids, cell) -> int:
    center = Point(cell[0], cell[1], srid=4326)
    return (
        DisplayedActeur.objects.all()
        .proposing(gestes, sous_categorie_ids)
        .physical()
        .filter(location__dwithin=(center, D(km=RADIUS_KM)))
        .count()
    )
