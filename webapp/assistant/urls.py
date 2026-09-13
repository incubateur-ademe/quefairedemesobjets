from django.urls import path

from assistant import views

app_name = "assistant"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("recherche", views.RechercheView.as_view(), name="recherche"),
    path("objet/<slug:slug>/", views.ProduitView.as_view(), name="produit"),
    path("solutions/", views.SolutionsView.as_view(), name="solutions"),
    path("lieu/<str:uuid>/", views.LieuView.as_view(), name="lieu"),
    path("lieux.geojson", views.LieuxGeoJSONView.as_view(), name="lieux-geojson"),
    path("recherche/objet", views.RechercheObjetView.as_view(), name="recherche-objet"),
    path(
        "recherche/adresse",
        views.RechercheAdresseView.as_view(),
        name="recherche-adresse",
    ),
]
