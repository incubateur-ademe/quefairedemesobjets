from time import perf_counter

from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control

from assistant.forms import LieuxForm
from qfdmd.models import ProduitPage
from qfdmo.models.acteur import MAX_PLACES_ON_MAP, DisplayedActeur


def sous_categorie_ids_for(slug: str) -> list[int]:
    """Sous-catégories of the fiche, to narrow the places to that objet.

    A fiche without sous-catégorie returns an empty list: the places are then
    not narrowed, rather than showing none.
    """
    page = ProduitPage.objects.live().filter(slug=slug).first()
    if page is None:
        raise Http404(f"unknown objet: {slug}")
    return list(page.sous_categorie_objet.values_list("id", flat=True))


@method_decorator(
    cache_control(public=True, max_age=300, stale_while_revalidate=60),
    name="dispatch",
)
class LieuxGeoJSONView(View):
    def get(self, request, *args, **kwargs):
        form = LieuxForm(request.GET)
        if not form.is_valid():
            return HttpResponseBadRequest(
                form.errors.as_json(), content_type="application/json"
            )
        params = form.cleaned_data

        sous_categorie_ids = (
            sous_categorie_ids_for(params["objet"]) if params["objet"] else []
        )

        acteurs = DisplayedActeur.objects.all().proposing(
            params["geste"], sous_categorie_ids
        )
        if params["bbox"]:
            acteurs = acteurs.within(params["bbox"])
        else:
            acteurs = acteurs.nearest_to(params["lon"], params["lat"])

        start = perf_counter()
        payload = acteurs.for_the_map(MAX_PLACES_ON_MAP).as_geojson()
        duration_ms = (perf_counter() - start) * 1000

        response = JsonResponse(payload)
        # Read by the browser (Network tab, PerformanceObserver) and by the
        # map's debug overlay.
        timing = f'acteurs;dur={duration_ms:.1f};desc="lieux"'
        response.headers["Server-Timing"] = timing
        return response
