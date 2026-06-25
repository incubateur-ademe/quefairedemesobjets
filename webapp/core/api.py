from typing import List, Optional

from ninja import NinjaAPI, Query, Router

from qfdmo.api import ActeurSchema
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
    response=List[ActeurSchema],
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


api.add_router("/qfdmod/", qfdmod_router, tags=["Que faire de mes objets (carte)"])
