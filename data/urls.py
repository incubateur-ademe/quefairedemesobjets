from django.urls import path

from data.views import (
    SuggestionGroupeStatusView,
    suggestion_groupe_details,
    update_suggestion_groupe_details,
)

app_name = "data"

urlpatterns = [
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/update/",
        update_suggestion_groupe_details,
        name="suggestion_groupe_update",
    ),
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/details/",
        suggestion_groupe_details,
        name="suggestion_groupe_details",
    ),
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/status/",
        SuggestionGroupeStatusView.as_view(),
        name="suggestion_groupe_status",
    ),
]
