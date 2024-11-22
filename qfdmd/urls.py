from django.urls import path

from qfdmd.views import HomeView, SynonymeDetailView, search_view

urlpatterns = [
    path("dechet/", HomeView.as_view(), name="home"),
    path("dechet/recherche", search_view, name="search"),
    path("dechet/<slug:slug>/", SynonymeDetailView.as_view(), name="synonyme-detail"),
]
