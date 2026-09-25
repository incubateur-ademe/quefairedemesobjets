from assistant.api import router as assistant_router
from ninja import NinjaAPI
from qfdmo.api import router as qfdmo_router
from stats.api import router as stats_router

api = NinjaAPI(title="Que faire de mes objets et déchets", version="0.0.2")
api.add_router("/qfdmo/", qfdmo_router, tags=["Que faire de mes objets"])
api.add_router("/stats", stats_router, tags=["KPI"])

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
api_v1.add_router("/", assistant_router, tags=["Assistant"])
