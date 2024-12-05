from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView

from qfdmd.views import HomeView, SynonymeDetailView, search_view

urlpatterns = [
    path("dechet/", HomeView.as_view(), name="home"),
    path("dechet/recherche", search_view, name="search"),
    path("dechet/<slug:slug>/", SynonymeDetailView.as_view(), name="synonyme-detail"),
    path(
        "assistant-enquete",
        RedirectView.as_view(
            url=settings.ASSISTANT_SURVEY_FORM, query_string=True, permanent=True
        ),
        name="assistant-survey-form",
    ),
]
