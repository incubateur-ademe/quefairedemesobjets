from django.conf import settings
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView

from qfdmd.views import HomeView, SynonymeDetailView, search_view


def get_assistant_script(request):
    return redirect(request.build_absolute_uri(static("assistant/script-to-iframe.js")))


urlpatterns = [
    path("dechet/", HomeView.as_view(), name="home"),
    path("dechet/recherche", search_view, name="search"),
    path("dechet/<slug:slug>/", SynonymeDetailView.as_view(), name="synonyme-detail"),
    path("script.js", get_assistant_script, name="script"),
    path(
        "assistant-enquete",
        RedirectView.as_view(
            url=settings.ASSISTANT_SURVEY_FORM, query_string=True, permanent=True
        ),
        name="assistant-survey-form",
    ),
]
