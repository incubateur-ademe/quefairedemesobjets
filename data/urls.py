from django.urls import path

from data.views import SuggestionGroupeStatusView, SuggestionGroupeView

app_name = "data"

urlpatterns = [
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/",
        SuggestionGroupeView.as_view(),
        name="suggestion_groupe",
    ),
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/<str:action>/status/",
        SuggestionGroupeStatusView.as_view(),
        name="suggestion_groupe_status",
    ),
]
