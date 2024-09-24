from django.conf import settings
from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from qfdmo.views.adresses import (
    AddressesView,
    adresse_detail,
    form_adresse_suggestion,
    get_object_list,
    getorcreate_revisionacteur,
    solution_admin,
)
from qfdmo.views.configurator import ConfiguratorView
from qfdmo.views.dags import DagsValidation

urlpatterns = [
    path("", AddressesView.as_view(), name="reemploi_solution"),
    path("connexion", LoginView.as_view(), name="login"),
    path(
        "formulaire-suggestion-adresse",
        form_adresse_suggestion,
        name="form-adresse-suggestion",
    ),
    path(
        "qfdmo/getorcreate_revisionacteur/<str:acteur_identifiant>",
        getorcreate_revisionacteur,
        name="getorcreate_revisionacteur",
    ),
    path(
        "qfdmo/refresh_acteur_view",
        RedirectView.as_view(url=settings.AIRFLOW_WEBSERVER_REFRESHACTEUR_URL),
        name="refresh_acteur_view",
    ),
    path(
        "qfdmo/get_object_list",
        get_object_list,
        name="get_object_list",
    ),
    path(
        "adresse/<str:identifiant_unique>",
        adresse_detail,
        name="adresse_detail",
    ),
    path(
        "solution_admin/<str:identifiant_unique>",
        solution_admin,
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
    path(
        "dags/validations",
        DagsValidation.as_view(),
        name="dags_validations",
    ),
    path(
        "iframe/configurateur",
        ConfiguratorView.as_view(),
        name="iframe_configurator",
    ),
]
