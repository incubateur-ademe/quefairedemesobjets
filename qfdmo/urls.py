from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from qfdmo.views import google_verification
from qfdmo.views.adresses import (
    CarteSearchActeursView,
    FormulaireSearchActeursView,
    acteur_detail,
    acteur_detail_redirect,
    direct_access,
    get_object_list,
    getorcreate_revisionacteur,
    solution_admin,
)
from qfdmo.views.auth import LVAOLoginView
from qfdmo.views.configurator import AdvancedConfiguratorView, ConfiguratorView
from qfdmo.views.dags import DagsValidation

urlpatterns = [
    path("", direct_access, name="direct_access"),
    path("carte", CarteSearchActeursView.as_view(), name="carte"),
    path("carte.json", CarteSearchActeursView.as_view(), name="carte_json"),
    path("formulaire", FormulaireSearchActeursView.as_view(), name="formulaire"),
    path("connexion", LVAOLoginView.as_view(), name="login"),
    path(settings.QFDMO_GOOGLE_SEARCH_CONSOLE, google_verification),
    path(
        "donnez-votre-avis",
        RedirectView.as_view(
            url=settings.FEEDBACK_FORM, query_string=True, permanent=True
        ),
        name="feedback-form",
    ),
    path(
        "proposer-une-adresse",
        RedirectView.as_view(
            url=settings.ADDRESS_SUGGESTION_FORM, query_string=True, permanent=True
        ),
        name="address-suggestion-form",
    ),
    path(
        "nous-contacter",
        RedirectView.as_view(
            url=settings.CONTACT_FORM, query_string=True, permanent=True
        ),
        name="contact-form",
    ),
    path(
        "proposer-une-modification",
        RedirectView.as_view(
            url=settings.UPDATE_SUGGESTION_FORM, query_string=True, permanent=True
        ),
        name="update-suggestion-form",
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
        acteur_detail_redirect,
    ),
    path(
        "adresse_details/<str:uuid>",
        acteur_detail,
        name="acteur-detail",
    ),
    path(
        "solution_admin/<str:identifiant_unique>",
        solution_admin,
        name="solution_admin",
    ),
    path(
        "test_iframe",
        TemplateView.as_view(template_name="tests/iframe.html"),
        name="test_iframe",
    ),
    path(
        "configurateur",
        ConfiguratorView.as_view(),
        name="iframe_configurator",
    ),
    path(
        "iframe/configurateur",
        AdvancedConfiguratorView.as_view(),
        name="advanced_iframe_configurator",
    ),
    # DEPRECATED, should use the data django app
    path(
        "dags/validations",
        DagsValidation.as_view(),
        name="dags_validations",
    ),
]
