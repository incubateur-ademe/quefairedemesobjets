from django.urls import path

from data.views import SuggestionManagement

urlpatterns = [
    path(
        "suggestions/",
        SuggestionManagement.as_view(),
        name="suggestions",
    ),
]
