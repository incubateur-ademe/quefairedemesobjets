from django.urls import path

from assistant import views

app_name = "assistant"

urlpatterns = [
    path("recherche/objet", views.ObjetSearchView.as_view(), name="recherche-objet"),
    path(
        "recherche/adresse",
        views.AdresseSearchView.as_view(),
        name="recherche-adresse",
    ),
]
