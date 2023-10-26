from django.urls import path

from qfdmo.views import corrections, display_solutions

urlpatterns = [
    path(
        "", display_solutions.ReemploiSolutionView.as_view(), name="reemploi_solution"
    ),
    path(
        "qfdmo/getorcreate_revisionacteur/<int:acteur_id>",
        display_solutions.getorcreate_revision_acteur,
        name="getorcreate_revisionacteur",
    ),
    path(
        "qfdmo/refresh_acteur_view",
        display_solutions.refresh_acteur_view,
        name="refresh_acteur_view",
    ),
    path(
        "qfdmo/get_object_list",
        display_solutions.get_object_list,
        name="get_object_list",
    ),
    path(
        "qfdmo/corrections",
        corrections.CorrectionsView.as_view(),
        name="display_corrections",
    ),
    path(
        "solution/<str:identifiant_unique>",
        display_solutions.solution_detail,
        name="solution_detail",
    ),
    path(
        "solution_admin/<str:identifiant_unique>",
        display_solutions.solution_admin,
        name="solution_admin",
    ),
]
