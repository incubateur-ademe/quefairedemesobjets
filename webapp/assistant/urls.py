"""Screens of the assistant. The JSON endpoints live in `assistant/api.py`,
mounted at `/api/v1/`."""

from django.urls import path

from assistant import views

app_name = "assistant"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("recherche/", views.SearchView.as_view(), name="recherche"),
    path("objet/<slug:slug>/", views.ProduitView.as_view(), name="produit"),
    path("solutions/", views.SolutionsView.as_view(), name="solutions"),
    path("lieu/<str:uuid>/", views.LieuView.as_view(), name="lieu"),
]
