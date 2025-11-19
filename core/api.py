from ninja import NinjaAPI

from qfdmd.api import router as qfdmd_router
from qfdmo.api import router as qfdmo_router
from stats.api import router as stats_router

api = NinjaAPI(title="Longue vie aux objets", version="0.0.2")
api.add_router("/qfdmo/", qfdmo_router, tags=["Que faire de mes objets"])
api.add_router("/qfdmd/", qfdmd_router, tags=["Que faire de mes déchets"])
api.add_router("/stats", stats_router, tags=["KPI"])
