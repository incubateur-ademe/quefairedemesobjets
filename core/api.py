from ninja import NinjaAPI
from qfdmd.api import router as qfdmd_router
from qfdmo.api import router as qfdmo_router


api = NinjaAPI(title="Longue vie aux objets", version="0.0.1")
api.add_router("/qfdmo/", qfdmo_router, tags=["Que faire de mes objets"])
api.add_router("/qfdmd/", qfdmd_router, tags=["Que faire de mes déchets"])
