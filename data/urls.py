from django.urls import path

from data.views import (
    SuggestionGroupeStatusView,
    SuggestionGroupeView,
    get_suggestion_groupe_usefull_links,
)

app_name = "data"

urlpatterns = [
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/",
        SuggestionGroupeView.as_view(),
        name="suggestion_groupe",
    ),
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/status/",
        SuggestionGroupeStatusView.as_view(),
        name="suggestion_groupe_status",
    ),
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/<str:usefull_link>/",
        get_suggestion_groupe_usefull_links,
        name="suggestion_groupe_usefull_links",
    ),
]
