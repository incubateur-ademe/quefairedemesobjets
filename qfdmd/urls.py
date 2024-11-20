from django.http import HttpResponse
from django.urls import path

from qfdmd.views import HomeView, SearchFormView, SynonymeDetailView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dechet/recherche", SearchFormView.as_view(), name="search"),
    path("success/", lambda _: HttpResponse("Success!"), name="success"),
    path("dechet/<slug:slug>/", SynonymeDetailView.as_view(), name="synonyme-detail"),
]
