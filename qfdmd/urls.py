from django.urls import path

from qfdmd.views import HomeView, SynonymeDetailView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dechet/<slug:slug>/", SynonymeDetailView.as_view(), name="synonyme-detail"),
]
