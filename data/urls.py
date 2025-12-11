from django.urls import path

from data.views import (
    GoogleStreetViewProxyView,
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
        "google-streetview-proxy/",
        GoogleStreetViewProxyView.as_view(),
        name="google_streetview_proxy",
    ),
]
