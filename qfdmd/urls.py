from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView

from qfdmd.views import (
    CMSPageDetailView,
    ContactFormView,
    HomeView,
    SynonymeDetailView,
    get_assistant_script,
    search_view,
)

urlpatterns = [
    path("dechet/", HomeView.as_view(), name="home"),
    path("assistant/recherche", search_view, name="search"),
    path("dechet/<slug:slug>/", SynonymeDetailView.as_view(), name="synonyme-detail"),
    path("assistant/nous-contacter", ContactFormView.as_view(), name="nous-contacter"),
    path(
        "assistant/nous-contacter/confirmation",
        ContactFormView.as_view(),
        name="nous-contacter-confirmation",
    ),
    # The URL here needs to be kept as is because it was used in the previous
    # Gatsby website. If changed, a redirect need to be created to keep the
    # legacy behaviour.
    path("iframe.js", get_assistant_script, name="script"),
    path("assistant/<slug:slug>", CMSPageDetailView.as_view(), name="cms-page"),
    path(
        "assistant-enquete",
        RedirectView.as_view(
            url=settings.ASSISTANT_SURVEY_FORM, query_string=True, permanent=True
        ),
        name="assistant-survey-form",
    ),
]
