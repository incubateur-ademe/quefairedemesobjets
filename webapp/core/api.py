from data.revue.api import router as revue_router
from data.revue.errors import RevueApiError, revue_api_error_handler
from ninja import NinjaAPI
from qfdmo.api import router as qfdmo_router
from stats.api import router as stats_router

api = NinjaAPI(title="Que faire de mes objets et déchets", version="0.0.2")
api.add_router("/qfdmo/", qfdmo_router, tags=["Que faire de mes objets"])
api.add_router("/stats", stats_router, tags=["KPI"])
api.add_router("/suggestions/", revue_router, tags=["Revue suggestions"])
api.add_exception_handler(RevueApiError, revue_api_error_handler)
