"""Open data API, version 1: what the site publishes for reuse.

The places of the acteurs dataset published on data.ademe.fr (`lieux.py`), as
paginated JSON. Mounted at `/api/v1/` next to the assistant's router
(`core/api.py`): same parameters as the assistant's screens
(`qfdmo/lieux_query.py`).
"""

from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from ninja import Query, Router
from ninja.decorators import decorate_view
from ninja.pagination import paginate

from opendata.lieux import GesteSchema, LieuSchema, for_the_api, open_data
from qfdmo.lieux_query import LieuxQuery
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import GroupeAction

router = Router()

CACHE_FIVE_MINUTES = cache_control(public=True, max_age=300, stale_while_revalidate=60)


@router.get(
    "/lieux",
    response=list[LieuSchema],
    url_name="lieux",
    summary="Lieux proposant un geste, du plus proche au plus lointain",
)
@decorate_view(CACHE_FIVE_MINUTES)
@paginate
def lieux(request, query: Query[LieuxQuery]):
    """Les mêmes lieux que l'assistant affiche, restreints aux sources sous
    licence ouverte : le périmètre du jeu de données publié sur data.ademe.fr.

    Triés par proximité du point donné, ou du centre de la zone `bbox`.
    """
    return for_the_api(open_data(query.queryset()))


@router.get(
    "/lieux/{identifiant}",
    response=LieuSchema,
    url_name="lieu",
    summary="Un lieu",
)
@decorate_view(CACHE_FIVE_MINUTES)
def lieu(request, identifiant: str):
    """Le lieu portant cet identifiant, s'il est sous licence ouverte."""
    acteurs = for_the_api(open_data(DisplayedActeur.objects.all()))
    return get_object_or_404(acteurs, uuid=identifiant)


@router.get(
    "/gestes",
    response=list[GesteSchema],
    url_name="gestes",
    summary="Les gestes, valeurs du paramètre `geste`",
)
def gestes(request):
    return GroupeAction.objects.order_by("order")
