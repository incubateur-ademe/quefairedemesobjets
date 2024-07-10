from ninja import NinjaAPI
from qfdmd.api import router as qfdmd_router

api = NinjaAPI()

api.add_router("/qfdmd/", qfdmd_router)
