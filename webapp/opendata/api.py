"""Open data API, version 1: what the site publishes for reuse.

The places of the acteurs dataset published on data.ademe.fr (`lieux.py`) and
the two tables of the fiches (`fiches.py`), as paginated JSON; the fiches also
as a whole CSV table with `Accept: text/csv`. Mounted at `/api/v1/`
(`core/api.py`).
"""

from functools import wraps
from io import StringIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.vary import vary_on_headers
from ninja import Query, Router, Schema
from ninja.decorators import decorate_view
from ninja.pagination import paginate

from core.http_cache import CACHE_FIVE_MINUTES, CACHE_ONE_HOUR
from opendata.fiches import (
    CONSIGNE_COLUMNS,
    PRODUIT_COLUMNS,
    all_consigne_rows,
    produit_rows,
    write_csv,
)
from opendata.lieux import GesteSchema, LieuSchema, for_the_api, open_data
from qfdmo.lieux_query import LieuxQuery
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import GroupeAction


class ProduitSchema(Schema):
    identifiant: int
    nom: str
    url: str
    type: str
    identifiant_famille: int | None = None
    synonymes: str
    sous_categories: str
    date_de_derniere_modification: str


class ConsigneSchema(Schema):
    identifiant: str
    identifiant_produit: int
    ordre: int
    titre: str
    contenu: str
    contenu_texte: str
    gestes: str
    etat: str
    lieu_de_depot: str
    bonus_reparation: bool
    lien_url: str


def _csv_response(rows, columns, filename) -> HttpResponse:
    stream = StringIO()
    write_csv(rows, columns, stream)
    response = HttpResponse(stream.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def csv_when_asked(rows, columns, filename):
    """The whole table as CSV when the client prefers `text/csv`, the
    paginated JSON otherwise (a browser's `*/*` gets JSON)."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            preferred = request.get_preferred_type(["application/json", "text/csv"])
            if preferred == "text/csv":
                return _csv_response(rows(), columns, filename)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def _csv_openapi(columns) -> dict:
    return {
        "responses": {
            200: {
                "description": "JSON paginé, ou la table entière en CSV avec "
                "`Accept: text/csv`",
                "content": {
                    "text/csv": {
                        "schema": {"type": "string"},
                        "example": ",".join(columns),
                    }
                },
            }
        }
    }


router = Router()


@router.get(
    "/lieux",
    response=list[LieuSchema],
    url_name="lieux",
    summary="Lieux proposant un geste, du plus proche au plus lointain",
)
@decorate_view(CACHE_FIVE_MINUTES)
@paginate
def lieux(request, query: Query[LieuxQuery]):
    """Les lieux sous licence ouverte, le périmètre du jeu de données publié
    sur data.ademe.fr, triés par proximité du point donné ou du centre de la
    zone `bbox`."""
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
@decorate_view(CACHE_ONE_HOUR)
def gestes(request):
    return GroupeAction.objects.order_by("order")


# Rows are rebuilt on every request: precompute them if the fiches grow past
# a few hundred.
@router.get(
    "/produits",
    response=list[ProduitSchema],
    url_name="produits",
    summary="Les fiches objets et déchets, paginées ou en CSV",
    openapi_extra=_csv_openapi(PRODUIT_COLUMNS),
)
@decorate_view(
    csv_when_asked(produit_rows, PRODUIT_COLUMNS, "produits.csv"),
    CACHE_ONE_HOUR,
    vary_on_headers("Accept"),
)
@paginate
def produits(request):
    """Les fiches publiées, familles comprises (`identifiant_famille`).
    `sous_categories` sont les codes du jeu de données des acteurs."""
    return produit_rows()


@router.get(
    "/consignes",
    response=list[ConsigneSchema],
    url_name="consignes",
    summary="Les consignes des fiches, paginées ou en CSV",
    openapi_extra=_csv_openapi(CONSIGNE_COLUMNS),
)
@decorate_view(
    csv_when_asked(all_consigne_rows, CONSIGNE_COLUMNS, "consignes.csv"),
    CACHE_ONE_HOUR,
    vary_on_headers("Accept"),
)
@paginate
def consignes(request):
    """Une ligne par consigne, `identifiant_produit` renvoyant à `/produits`.
    `gestes` porte les codes d'action du jeu de données des acteurs."""
    return all_consigne_rows()
