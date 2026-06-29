from typing import List, Optional

from ninja import Field, NinjaAPI, Query, Router, Schema

from qfdmd.views import AutocompleteHomeSearchView
from qfdmo.api import CarteActeurSchema, SousCategorieObjetSchema
from qfdmo.api import router as qfdmo_router
from qfdmo.models import SousCategorieObjet
from qfdmo.models.action import Action
from qfdmo.views.carte import CarteSearchActeursView
from stats.api import router as stats_router

api = NinjaAPI(title="Que faire de mes objets et déchets", version="0.0.2")
api.add_router("/qfdmo/", qfdmo_router, tags=["Que faire de mes objets"])
api.add_router("/stats", stats_router, tags=["KPI"])

qfdmod_router = Router()


class ApiCarteSearchActeursView(CarteSearchActeursView):
    """Drive ``CarteSearchActeursView`` from explicit API query parameters
    instead of the prefixed form fields used by the HTML carte."""

    def __init__(
        self,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        action_codes: list[str] | None = None,
        sous_categorie_codes: list[str] | None = None,
    ):
        super().__init__()
        self._api_latitude = latitude
        self._api_longitude = longitude
        self._api_action_codes = action_codes or []
        self._api_sous_categorie_codes = sous_categorie_codes or []

    def _get_latitude(self):
        return self._api_latitude

    def _get_longitude(self):
        return self._api_longitude

    def _get_bounding_box(self):
        return None

    def _get_epci_codes(self) -> list[str]:
        return []

    def _get_action_ids(self) -> list[int]:
        if not self._api_action_codes:
            return []
        return list(
            Action.objects.filter(code__in=self._api_action_codes).values_list(
                "id", flat=True
            )
        )

    def _get_sous_categorie_ids(self) -> list[int]:
        if not self._api_sous_categorie_codes:
            return []
        return list(
            SousCategorieObjet.objects.filter(
                code__in=self._api_sous_categorie_codes
            ).values_list("id", flat=True)
        )


@qfdmod_router.get(
    "/acteurs",
    response=List[CarteActeurSchema],
    summary="Acteurs de la recherche carte",
)
def carte_acteurs(
    request,
    latitude: float | None = None,
    longitude: float | None = None,
    action: Optional[List[str]] = Query(
        None, description="Codes d'action (ex: reparer, donner)"
    ),
    sous_categorie: Optional[List[str]] = Query(
        None, description="Codes de sous-catégories d'objet"
    ),
):
    """
    Retourne la liste des acteurs correspondant aux paramètres de recherche de
    la carte, en s'appuyant sur ``CarteSearchActeursView.get_context_data``.

    - ``latitude`` / ``longitude`` : centre de la recherche (obligatoires pour
      obtenir des résultats, sinon la liste est vide).
    - ``action`` : un ou plusieurs codes d'action pour filtrer.
    - ``sous_categorie`` : un ou plusieurs codes de sous-catégorie d'objet.
    """
    view = ApiCarteSearchActeursView(
        latitude=latitude,
        longitude=longitude,
        action_codes=action,
        sous_categorie_codes=sous_categorie,
    )
    view.setup(request)
    context = view.get_context_data()

    acteurs = context.get("acteurs")
    if acteurs is None and (paginated := context.get("paginated_acteurs_obj")):
        acteurs = paginated.object_list

    return acteurs or []


class ApiAutocompleteHomeSearchView(AutocompleteHomeSearchView):
    """Drive ``AutocompleteHomeSearchView`` from an explicit API query
    parameter instead of the ``q`` form field used by the homepage search."""

    def __init__(self, *, query: str | None = None):
        super().__init__()
        self._api_query = query or ""

    def _get_search_query(self) -> str:
        return self._api_query


class AutocompleteResultSchema(Schema):
    id: int = Field(..., description="Identifiant du terme de recherche")
    nom: str = Field(..., alias="title", description="Le libellé affiché")
    type: str = Field(..., alias="kind", description="Le type de terme de recherche")
    lien: Optional[str] = Field(
        None,
        alias="redirect_destination",
        description="L'URL de destination associée au terme de recherche",
    )


class AutocompleteSousCategorieSchema(Schema):
    id: int = Field(..., description="Identifiant du terme de recherche")
    nom: str = Field(..., alias="title", description="Le libellé affiché")
    type: str = Field(..., alias="kind", description="Le type de terme de recherche")
    sous_categories: List[SousCategorieObjetSchema] = Field(
        ...,
        description="Les sous-catégories d'objet associées au terme de recherche",
    )


@qfdmod_router.get(
    "/autocomplete",
    response=List[AutocompleteResultSchema],
    summary="Autocomplétion de la recherche d'accueil",
)
def autocomplete(request, q: str | None = None):
    """
    Retourne les suggestions d'autocomplétion de la recherche d'accueil
    (« Que faire de mes objets et déchets ») en s'appuyant sur
    ``AutocompleteHomeSearchView``.

    - ``q`` : le texte saisi par l'utilisateur. Si vide, la liste est vide.
    """
    view = ApiAutocompleteHomeSearchView(query=q)
    view.setup(request)
    results = view.get_queryset()

    # Resolve the most specific child instance for each SearchTerm so that the
    # `title`, `kind` and `redirect_destination` reflect the real content type.
    return [result.specific for result in results if result.specific]


@qfdmod_router.get(
    "/autocomplete/sous-categories",
    response=List[AutocompleteSousCategorieSchema],
    summary="Sous-catégories associées aux termes de l'autocomplétion",
)
def autocomplete_sous_categories(request, q: str | None = None):
    """
    Pour chaque terme retourné par l'autocomplétion de la recherche d'accueil,
    renvoie les sous-catégories d'objet associées (via le produit ou la page
    produit liée).

    - ``q`` : le texte saisi par l'utilisateur. Si vide, la liste est vide.
    """
    view = ApiAutocompleteHomeSearchView(query=q)
    view.setup(request)
    results = view.get_queryset()

    return [result.specific for result in results if result.specific]


api.add_router("/qfdmod/", qfdmod_router, tags=["Que faire de mes objets (carte)"])
