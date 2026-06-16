from data.views import (
    CohortAdminListView,
    CohorteReviewBulkView,
    CohorteReviewGroupeView,
    CohorteReviewRowsView,
    CohorteReviewView,
    SuggestionGroupeStatusView,
    SuggestionGroupeView,
)
from django.urls import path

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
        "cohorte/",
        CohortAdminListView.as_view(),
        name="cohorte_admin_list",
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
    path(
        "cohorte/<int:cohorte_id>/review/groupe/<int:groupe_id>/",
        CohorteReviewGroupeView.as_view(),
        name="cohorte_review_groupe",
    ),
]
