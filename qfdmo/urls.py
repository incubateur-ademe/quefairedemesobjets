from django.conf import settings
from django.urls import path
from django.views.generic.base import RedirectView

from qfdmo.views import (
    get_carte_iframe_script,
    get_formulaire_iframe_script,
    google_verification,
)
from qfdmo.views.adresses import (
    acteur_detail,
    acteur_detail_redirect,
    get_synonyme_list,
    getorcreate_revisionacteur,
    solution_admin,
)
from qfdmo.views.carte import CarteConfigView, CarteSearchActeursView
from qfdmo.views.configurator import AdvancedConfiguratorView, ConfiguratorView
from qfdmo.views.formulaire import FormulaireSearchActeursView

urlpatterns = [
    # This route needs to be touched with care is it is embedded
    # on many website, enabling the load of Carte / Formulaire as an iframe
    path("static/carte.js", get_carte_iframe_script, name="carte_script"),
    path("static/iframe.js", get_formulaire_iframe_script, name="formulaire_script"),
    path("carte", CarteSearchActeursView.as_view(), name="carte"),
    path("carte/<slug:slug>/", CarteConfigView.as_view(), name="carte_custom"),
    path("carte.json", CarteSearchActeursView.as_view(), name="carte_json"),
    path("formulaire", FormulaireSearchActeursView.as_view(), name="formulaire"),
    path(settings.CARTE.get("GOOGLE_SEARCH_CONSOLE"), google_verification),
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
        "qfdmo/get_synonyme_list",
        get_synonyme_list,
        name="get_synonyme_list",
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
        "configurateur",
        ConfiguratorView.as_view(),
        name="iframe_configurator",
    ),
    path(
        "iframe/configurateur",
        AdvancedConfiguratorView.as_view(),
        name="advanced_iframe_configurator",
    ),
]
