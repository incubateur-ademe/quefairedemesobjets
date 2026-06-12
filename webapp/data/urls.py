from django.urls import path

from data.views import (
    CohorteReviewBulkView,
    CohorteReviewRowsView,
    CohorteReviewView,
    SuggestionGroupeStatusView,
    SuggestionGroupeView,
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
        "cohorte/<int:cohorte_id>/review/",
        CohorteReviewView.as_view(),
        name="cohorte_review",
    ),
    path(
        "cohorte/<int:cohorte_id>/review/rows/",
        CohorteReviewRowsView.as_view(),
        name="cohorte_review_rows",
    ),
    path(
        "cohorte/<int:cohorte_id>/review/bulk/",
        CohorteReviewBulkView.as_view(),
        name="cohorte_review_bulk",
    ),
]
