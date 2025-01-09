from django.urls import path

from data.views import DagsValidation

urlpatterns = [
    path(
        "dags/validations",
        DagsValidation.as_view(),
        name="dags_validations",
    ),
]
