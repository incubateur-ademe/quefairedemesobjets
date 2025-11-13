from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView

from qfdmd.views import (
    HomeView,
    SynonymeDetailView,
    contrib_displayed_acteur,
    get_assistant_script,
    search_view,
)
from qfdmo.views.carte import ProductCarteView

urlpatterns = [
    path("assistant/recherche", search_view, name="search"),
    path(
        "assistant-enquete",
        RedirectView.as_view(
            url=settings.ASSISTANT_SURVEY_FORM, query_string=True, permanent=True
        ),
        name="assistant-survey-form",
    ),
    path("dechet", RedirectView.as_view(url="/", query_string=True, permanent=True)),
    # The URL here needs to be kept as is because it was used in the previous
    # Gatsby website. If changed, a redirect need to be created to keep the
    # legacy behaviour.
    path("dechet/<slug:slug>/", SynonymeDetailView.as_view(), name="synonyme-detail"),
    path("dechet/<slug:slug>/carte/", ProductCarteView.as_view(), name="carte"),
    path("update-acteur", contrib_displayed_acteur, name="contrib"),
    path("iframe.js", get_assistant_script, name="script"),
    path("", HomeView.as_view(), name="home"),
]
