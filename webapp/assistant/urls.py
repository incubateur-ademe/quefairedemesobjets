from django.urls import path

from assistant import views

app_name = "assistant"

urlpatterns = [
    path("lieux.geojson", views.LieuxGeoJSONView.as_view(), name="lieux-geojson"),
    path("recherche/objet", views.RechercheObjetView.as_view(), name="recherche-objet"),
]
