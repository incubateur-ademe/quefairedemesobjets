from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control

from qfdmd.models import ProduitPage
from qfdmo.map_utils import sanitize_frontend_bbox
from qfdmo.models.acteur import NOMBRE_MAX_LIEUX, DisplayedActeur


class InvalidPosition(ValueError):
    pass


def sous_categorie_ids_for(slug: str) -> list[int]:
    """Sous-catégories de la fiche, pour restreindre les lieux à cet objet.

    Une fiche sans sous-catégorie renvoie une liste vide : les lieux ne sont
    alors pas restreints, plutôt que de n'en afficher aucun.
    """
    page = ProduitPage.objects.live().filter(slug=slug).first()
    if page is None:
        raise Http404(f"objet inconnu : {slug}")
    return list(page.sous_categorie_objet.values_list("id", flat=True))


def position_from(query) -> dict:
    """Lit la position demandée, en donnant la priorité à la zone visible.

    Une bbox illisible est refusée plutôt que rabattue sur lat/lon : le repli
    masquerait un bug client et afficherait une zone que l'usager ne regarde
    pas.
    """
    if raw_bbox := query.get("bbox"):
        bbox = sanitize_frontend_bbox(raw_bbox)
        if not bbox:
            raise InvalidPosition("bbox")
        return {"bbox": bbox, "longitude": None, "latitude": None}

    try:
        return {
            "bbox": None,
            "longitude": float(query["lon"]),
            "latitude": float(query["lat"]),
        }
    except (KeyError, TypeError, ValueError) as erreur:
        raise InvalidPosition("lat/lon") from erreur


@method_decorator(
    cache_control(public=True, max_age=300, stale_while_revalidate=60),
    name="dispatch",
)
class LieuxGeoJSONView(View):
    def get(self, request, *args, **kwargs):
        geste = request.GET.get("geste")
        if not geste:
            return HttpResponseBadRequest("geste manquant")

        try:
            position = position_from(request.GET)
        except InvalidPosition as erreur:
            return HttpResponseBadRequest(f"position invalide : {erreur}")

        sous_categorie_ids = (
            sous_categorie_ids_for(objet) if (objet := request.GET.get("objet")) else []
        )

        lieux = DisplayedActeur.objects.all().proposing(geste, sous_categorie_ids)
        if position["bbox"]:
            lieux = lieux.within(position["bbox"])
        else:
            lieux = lieux.nearest_to(position["longitude"], position["latitude"])

        return JsonResponse(lieux.for_the_map(NOMBRE_MAX_LIEUX).as_geojson())
