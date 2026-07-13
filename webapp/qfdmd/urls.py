from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView

from qfdmd.views import (
    AutocompleteHomeSearchView,
    HomeView,
    dechet_detail,
    get_assistant_script,
)

urlpatterns = [
    path(
        "assistant/autocomplete-search",
        AutocompleteHomeSearchView.as_view(),
        name="autocomplete_home_search",
    ),
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
    # Wagtail is given priority on this route (migrated ProduitPage live
    # under the /dechet index page); dechet_detail falls back to the legacy
    # SynonymeDetailView when no Wagtail page matches.
    path("dechet/<slug:slug>/", dechet_detail, name="synonyme-detail"),
    path("iframe.js", get_assistant_script, name="script"),
    path("", HomeView.as_view(), name="home"),
]
