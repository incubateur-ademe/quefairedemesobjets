from django.urls import path
from django.views.generic import TemplateView

from qfdmo.views import corrections, display_solutions

urlpatterns = [
    path(
        "", display_solutions.ReemploiSolutionView.as_view(), name="reemploi_solution"
    ),
    path(
        "qfdmo/getorcreate_revisionacteur/<str:acteur_identifiant>",
        display_solutions.getorcreate_correctionequipeacteur,
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
        "corrections",
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
    path(
        "plandusite",
        TemplateView.as_view(template_name="editorial/sitemap.html"),
        name="sitemap",
    ),
    path(
        "accessibilite",
        TemplateView.as_view(template_name="editorial/accessibility.html"),
        name="accessibility",
    ),
    path(
        "mentionslegales",
        TemplateView.as_view(template_name="editorial/legal_notices.html"),
        name="legal_notices",
    ),
    path(
        "donneespersonnelles",
        TemplateView.as_view(template_name="editorial/personal_data.html"),
        name="personal_data",
    ),
    path(
        "cookies",
        TemplateView.as_view(template_name="editorial/cookies.html"),
        name="cookies",
    ),
    path(
        "cgu",
        TemplateView.as_view(template_name="editorial/cgu.html"),
        name="cgu",
    ),
]
