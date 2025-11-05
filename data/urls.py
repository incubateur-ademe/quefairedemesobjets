from django.urls import path

from . import views

app_name = "data"

urlpatterns = [
    path(
        "suggestion-groupe/<int:suggestion_groupe_id>/refresh/",
        views.refresh_suggestion_groupe,
        name="refresh_suggestion_groupe",
    ),
]
