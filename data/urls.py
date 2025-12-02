from django.urls import path

from data.views import (
    SuggestionGroupeStatusView,
    SuggestionGroupeView,
    get_suggestion_groupe_usefull_links,
    update_suggestion_groupe_details,
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
        "suggestion-groupe/<int:suggestion_groupe_id>/update/",
        update_suggestion_groupe_details,
        name="suggestion_groupe_update",
    ),
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/<str:usefull_link>/",
        get_suggestion_groupe_usefull_links,
        name="suggestion_groupe_usefull_links",
    ),
]
