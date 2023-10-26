from django.urls import path

from qfdmo.views import corrections, main_map

urlpatterns = [
    path("", main_map.ReemploiSolutionView.as_view(), name="reemploi_solution"),
    path(
        "qfdmo/getorcreate_revisionacteur/<int:acteur_id>",
        main_map.getorcreate_revision_acteur,
        name="getorcreate_revisionacteur",
    ),
    path(
        "qfdmo/refresh_acteur_view",
        main_map.refresh_acteur_view,
        name="refresh_acteur_view",
    ),
    path(
        "qfdmo/get_object_list",
        main_map.get_object_list,
        name="get_object_list",
    ),
    path(
        "qfdmo/corrections",
        corrections.CorrectionsView.as_view(),
        name="display_corrections",
    ),
]
