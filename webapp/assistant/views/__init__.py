from .adresse import RechercheAdresseView
from .geojson import LieuxGeoJSONView
from .pages import HomeView, LieuView, ProduitView, RechercheView, SolutionsView
from .recherche import RechercheObjetView

__all__ = [
    "HomeView",
    "LieuView",
    "LieuxGeoJSONView",
    "ProduitView",
    "RechercheAdresseView",
    "RechercheView",
    "RechercheObjetView",
    "SolutionsView",
]
