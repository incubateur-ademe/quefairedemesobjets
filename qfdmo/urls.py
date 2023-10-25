from django.urls import path

from . import views

urlpatterns = [
    path("", views.ReemploiSolutionView.as_view(), name="reemploi_solution"),
    path(
        "qfdmo/getorcreate_revisionacteur/<int:acteur_id>",
        views.getorcreate_revision_acteur,
        name="getorcreate_revisionacteur",
    ),
    path(
        "qfdmo/refresh_acteur_view",
        views.refresh_acteur_view,
        name="refresh_acteur_view",
    ),
    path(
        "qfdmo/get_object_list",
        views.get_object_list,
        name="get_object_list",
    ),
    path(
        "qfdmo/corrections",
        views.display_corrections,
        name="display_corrections",
    ),
]
