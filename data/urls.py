from django.urls import path

from data.views import SuggestionManagment

urlpatterns = [
    path(
        "suggestions",
        SuggestionManagment.as_view(),
        name="suggestions",
    ),
]
