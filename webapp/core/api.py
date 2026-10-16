from data.revue.api import router as revue_router
from data.revue.errors import RevueApiError, revue_api_error_handler
from ninja import NinjaAPI
from opendata.api import router as opendata_router
from qfdmo.api import router as qfdmo_router
from stats.api import router as stats_router

api = NinjaAPI(title="Que faire de mes objets et déchets", version="0.0.2")
api.add_router("/qfdmo/", qfdmo_router, tags=["Que faire de mes objets"])
api.add_router("/stats", stats_router, tags=["KPI"])
api.add_router("/suggestions/", revue_router, tags=["Revue suggestions"])
api.add_exception_handler(RevueApiError, revue_api_error_handler)

# Public API, versioned: the contract reusers build on. A separate instance so
# it has its own documentation page and the historical API can retire alone.
api_v1 = NinjaAPI(
    title="Que faire de mes objets et déchets",
    version="1",
    urls_namespace="api_v1",
    description=(
        "Les lieux, gestes et objets de l'assistant au tri, au réemploi et à la"
        " réparation. Mêmes paramètres et même moteur que l'assistant lui-même ;"
        " les lieux sont ceux du jeu de données ouvert publié sur data.ademe.fr."
    ),
)
api_v1.add_router("/", opendata_router, tags=["Open data"])
