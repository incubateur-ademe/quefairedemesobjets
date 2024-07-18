from ninja import NinjaAPI
from qfdmd.api import router as qfdmd_router


api = NinjaAPI(title="Longue vie aux objets", version="0.0.1")

api.add_router("/qfdmd/", qfdmd_router)
