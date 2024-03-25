from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from qfdmo.views import display_solutions

urlpatterns = [
    path(
        "", display_solutions.ReemploiSolutionView.as_view(), name="reemploi_solution"
    ),
    path(
        "qfdmo/getorcreate_revisionacteur/<str:acteur_identifiant>",
        #        display_solutions.getorcreate_correctionequipeacteur,
        display_solutions.getorcreate_revisionacteur,
        name="getorcreate_revisionacteur",
    ),
    path(
        "qfdmo/refresh_acteur_view",
        RedirectView.as_view(url=settings.AIRFLOW_WEBSERVER_REFRESHACTEUR_URL),
        name="refresh_acteur_view",
    ),
    path(
        "qfdmo/get_object_list",
        display_solutions.get_object_list,
        name="get_object_list",
    ),
    path(
        "adresse/<str:identifiant_unique>",
        display_solutions.adresse_detail,
        name="adresse_detail",
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
    path(
        "test_iframe",
        TemplateView.as_view(template_name="tests/iframe.html"),
        name="test_iframe",
    ),
]
