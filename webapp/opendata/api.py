"""Open data API, version 1: what the site publishes for reuse.

The two tables of the fiches (`fiches.py`), as paginated JSON and as CSV.
Mounted at `/api/v1/` (`core/api.py`).
"""

from io import StringIO

from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from ninja import Router, Schema
from ninja.decorators import decorate_view
from ninja.pagination import paginate

from opendata.fiches import (
    CONSIGNE_COLUMNS,
    PRODUIT_COLUMNS,
    all_consigne_rows,
    produit_rows,
    write_csv,
)

router = Router()


# Editorial content, published a few times a week at most.
CACHE_ONE_HOUR = cache_control(public=True, max_age=3600, stale_while_revalidate=300)


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


# ponytail: the rows of every fiche are built per request, a few hundred
# pages; cache them in a table if the fiches grow past that.
@router.get(
    "/produits",
    response=list[ProduitSchema],
    url_name="produits",
    summary="Les fiches objets et déchets, paginées",
)
@decorate_view(CACHE_ONE_HOUR)
@paginate
def produits(request):
    """Les fiches publiées, familles comprises (`identifiant_famille`).
    `sous_categories` sont les codes du jeu de données des acteurs."""
    return produit_rows()


@router.get(
    "/produits.csv",
    url_name="produits-csv",
    summary="Les fiches, en CSV",
)
@decorate_view(CACHE_ONE_HOUR)
def produits_csv(request):
    return _csv_response(produit_rows(), PRODUIT_COLUMNS, "produits.csv")


@router.get(
    "/consignes",
    response=list[ConsigneSchema],
    url_name="consignes",
    summary="Les consignes des fiches, paginées",
)
@decorate_view(CACHE_ONE_HOUR)
@paginate
def consignes(request):
    """Une ligne par consigne, `identifiant_produit` renvoyant à `/produits`.
    `gestes` porte les codes d'action du jeu de données des acteurs."""
    return all_consigne_rows()


@router.get(
    "/consignes.csv",
    url_name="consignes-csv",
    summary="Les consignes, en CSV",
)
@decorate_view(CACHE_ONE_HOUR)
def consignes_csv(request):
    return _csv_response(all_consigne_rows(), CONSIGNE_COLUMNS, "consignes.csv")
