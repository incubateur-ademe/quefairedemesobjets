import json
import logging
from typing import List, cast

import unidecode
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance
from django.core.cache import cache
from django.db.models import Q
from django.db.models.functions import Length, Lower
from django.db.models.query import QuerySet
from django.forms import model_to_dict
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls.base import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET
from django.views.generic.list import ListView

from core.jinja2_handler import distance_to_acteur
from core.utils import get_direction
from qfdmo.forms import CarteForm, FormulaireForm
from qfdmo.geo_api import bbox_from_list_of_geojson, retrieve_epci_geojson
from qfdmo.leaflet import (
    center_from_leaflet_bbox,
    compile_leaflet_bbox,
    sanitize_leaflet_bbox,
)
from qfdmo.models import (
    Acteur,
    ActeurStatus,
    Action,
    DisplayedActeur,
    Objet,
    RevisionActeur,
)
from qfdmo.models.action import (
    GroupeAction,
    get_action_instances,
    get_groupe_action_instances,
    get_reparer_action_id,
)
from qfdmo.thread.materialized_view import RefreshMateriazedViewThread

logger = logging.getLogger(__name__)

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


def direct_access(request):
    get_params = request.GET.copy()

    if "carte" in request.GET:
        # Order matters, this should be before iframe because iframe and carte
        # parameters can coexist
        del get_params["carte"]
        try:
            del get_params["iframe"]
        except KeyError:
            pass
        params = get_params.urlencode()
        parts = [reverse("qfdmo:carte"), "?" if params else "", params]
        return redirect("".join(parts))

    if "iframe" in request.GET:
        del get_params["iframe"]
        params = get_params.urlencode()
        parts = [reverse("qfdmo:formulaire"), "?" if params else "", params]
        return redirect("".join(parts))

    return redirect("https://longuevieauxobjets.ademe.fr/lacarte", permanent=True)


class DigitalMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(is_digital=self.request.GET.get("digital") == "1")

        return context


class TurboFormMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.turbo = request.headers.get("Turbo-Frame")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.turbo:
            context.update(turbo=True, base_template="layout/turbo.html")
        else:
            context.update(base_template="layout/base.html")

        return context


class ActeursListView(
    DigitalMixin,
    TurboFormMixin,
    ListView,
):
    # TODO : supprimer
    is_iframe = False
    is_carte = False
    is_embedded = True

    action_displayed: str = ""
    action_list: str = ""
    adresse: str | None = ""
    bonus: bool = False
    bounding_box: str = ""
    digital: str = "0"
    direction: str | None = None
    epci_codes: str = ""
    ess: bool = False
    grouped_action: list[str] = []  # list ?
    label_reparacteur: bool = False
    latitude: float | None = 0.0
    legend_grouped_action: list[str] = []  # list ?
    longitude: float | None = 0.0
    pas_exclusivite_reparation: bool = False
    sc_id: int | None = None
    sous_categorie_objet: str = ""
    request: HttpRequest

    def setup(self, request, *args, **kwargs):

        # FIXME : on peut certainement faire mieux
        self.request = request

        self.sous_categorie_objet = request.GET.get("sous_categorie_objet")
        self.adresse = request.GET.get("adresse")
        self.digital = request.GET.get("digital", "0")
        self.direction = get_direction(request, self.is_carte)
        self.latitude = request.GET.get("latitude")
        self.longitude = request.GET.get("longitude")
        self.label_reparacteur = bool(request.GET.get("label_reparacteur"))
        self.epci_codes = request.GET.getlist("epci_codes")

        self.pas_exclusivite_reparation = bool(
            request.GET.get("pas_exclusivite_reparation", True)
        )
        self.bonus = bool(request.GET.get("bonus"))
        self.ess = bool(request.GET.get("ess"))
        self.bounding_box = request.GET.get("bounding_box", "")
        self.sc_id = (
            int(request.GET.get("sc_id", ""))
            if request.GET.get("sc_id", "").isnumeric()
            else None
        )

        return super().setup(request, *args, **kwargs)

    def get_queryset(self):
        # Manage the selection of sous_categorie_objet and actions
        acteurs = self._acteurs_from_sous_categorie_objet_and_actions()
        if self.digital == "1":
            acteurs = acteurs.digital()[:100]
        else:
            bbox, acteurs = self._bbox_and_acteurs_from_location_or_epci(acteurs)
            acteurs = acteurs[: self._get_max_displayed_acteurs()]
        return acteurs

    def get_context_data(self, **kwargs):
        kwargs.update(
            # TODO: refacto forms : define a BooleanField carte on CarteAddressesForm
            carte=self.is_carte,
            # TODO: refacto forms, return bounded form in template
            # form=form,
            location="{}",
        )

        # Manage the selection of sous_categorie_objet and actions
        acteurs = self._acteurs_from_sous_categorie_objet_and_actions()

        if self.digital == "1":
            acteurs = acteurs.digital()[:100]
        else:
            bbox, acteurs = self._bbox_and_acteurs_from_location_or_epci(acteurs)
            acteurs = acteurs[: self._get_max_displayed_acteurs()]

            # Set Home location (address set as input)
            # FIXME : can be manage in template using the form value ?
            if (latitude := self.latitude) and (longitude := self.longitude):
                kwargs.update(
                    location=json.dumps({"latitude": latitude, "longitude": longitude})
                )
        # TODO : refacto forms, gérer ça autrement
        try:
            if bbox is None:
                kwargs["form"].initial["bounding_box"] = None
        except NameError:
            pass

        kwargs.update(acteurs=acteurs)
        # FIXME : on peut certainement faire mieux
        kwargs.update(object_list=acteurs)
        return super().get_context_data(**kwargs)

    def _bbox_and_acteurs_from_location_or_epci(self, acteurs):
        custom_bbox = cast(str, self.bounding_box)
        center = center_from_leaflet_bbox(custom_bbox)
        latitude = center[1] or self.latitude
        longitude = center[0] or self.longitude
        if custom_bbox:
            bbox = sanitize_leaflet_bbox(custom_bbox)
            acteurs_in_bbox = acteurs.in_bbox(bbox)

            if acteurs_in_bbox.count() > 0:
                return custom_bbox, acteurs_in_bbox

        # TODO
        # - Tester cas avec bounding box définie depuis le configurateur
        # - Tester cas avec center retourné par leaflet
        if latitude and longitude:
            acteurs_from_center = acteurs.from_center(longitude, latitude)
            if acteurs_from_center.count():
                custom_bbox = None

            return custom_bbox, acteurs_from_center

        if epci_codes := self.epci_codes:
            geojson_list = [retrieve_epci_geojson(code) for code in epci_codes]
            bbox = bbox_from_list_of_geojson(geojson_list, buffer=0)
            if geojson_list:
                acteurs = acteurs.in_geojson(
                    [json.dumps(geojson) for geojson in geojson_list]
                )
            return compile_leaflet_bbox(bbox), acteurs

        return custom_bbox, acteurs.none()

    def _get_max_displayed_acteurs(self):
        limit = self.request.GET.get("limit", "")
        if limit.isnumeric():
            return int(limit)
        if self.is_carte:
            return settings.CARTE_MAX_SOLUTION_DISPLAYED
        return settings.DEFAULT_MAX_SOLUTION_DISPLAYED

    def _set_action_displayed(self) -> List[Action]:
        cached_action_instances = cast(
            List[Action], cache.get_or_set("action_instances", get_action_instances)
        )
        """
        Limit to actions of the direction only in Carte mode
        """
        if direction := self.request.GET.get("direction"):
            if self.is_carte:
                cached_action_instances = [
                    action
                    for action in cached_action_instances
                    if direction in [d.code for d in action.directions.all()]
                ]
        if self.action_displayed:
            cached_action_instances = [
                action
                for action in cached_action_instances
                if action.code in self.action_displayed.split("|")
            ]
        # In form mode, only display actions with afficher=True
        # TODO : discuss with epargnonsnosressources if we can remove this condition
        # or set it in get_action_instances
        if not self.is_carte:
            cached_action_instances = [
                action for action in cached_action_instances if action.afficher
            ]
        return cached_action_instances

    def _set_action_list(self, action_displayed: List[Action]) -> List[Action]:
        if action_list := self.request.GET.get("action_list", ""):
            return [
                action
                for action in action_displayed
                if action.code in action_list.split("|")
            ]
        return action_displayed

    def _get_selected_action_code(self):
        """
        Get the action to include in the request
        """
        # FIXME : est-ce possible d'optimiser en accédant au valeur initial du form ?

        # selection from interface
        if self.grouped_action:
            return [
                code
                for new_groupe_action in self.grouped_action
                for code in new_groupe_action.split("|")
            ]
        # Selection is not set in interface, get all available from
        # (checked_)action_list
        if self.action_list:
            return self.action_list.split("|")
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        if self.action_displayed:
            return self.action_displayed.split("|")
        # return empty array, will search in all actions
        return []

    def _get_selected_action(self) -> List[Action]:
        """
        Get the action to include in the request
        """

        codes = []
        # selection from interface
        if self.request.GET.get("grouped_action"):
            codes = [
                code
                for new_groupe_action in self.request.GET.getlist("grouped_action")
                for code in new_groupe_action.split("|")
            ]

        # Selection is not set in interface, get all available from
        # (checked_)action_list
        elif action_list := self.action_list:
            # TODO : effet de bord si la list des action n'est pas cohérente avec
            # les actions affichées
            # il faut collecté les actions coché selon les groupes d'action
            codes = action_list.split("|")
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        elif action_displayed := self.action_displayed:
            codes = action_displayed.split("|")
        # return empty array, will search in all actions
        # Cast needed because of the cache
        cached_action_instances = cast(
            List[Action], cache.get_or_set("action_instances", get_action_instances)
        )
        actions = (
            [a for a in cached_action_instances if a.code in codes]
            if codes
            else cached_action_instances
        )
        if direction := self.request.GET.get("direction"):
            actions = [
                a for a in actions if direction in [d.code for d in a.directions.all()]
            ]
        return actions

    def _acteurs_from_sous_categorie_objet_and_actions(
        self,
    ) -> QuerySet[DisplayedActeur]:
        selected_actions_ids = self._get_selected_action_ids()
        reparer_action_id = cache.get_or_set("reparer_action_id", get_reparer_action_id)
        reparer_is_checked = reparer_action_id in selected_actions_ids

        filters, excludes = self._compile_acteurs_queryset(
            reparer_is_checked, selected_actions_ids, reparer_action_id
        )
        acteurs = DisplayedActeur.objects.exclude(excludes).filter(filters)
        if reparer_is_checked:
            acteurs = acteurs.with_reparer().with_bonus()

        acteurs = acteurs.prefetch_related(
            "proposition_services__sous_categories",
            "proposition_services__sous_categories__categorie",
            "proposition_services__action",
            "action_principale",
        ).distinct()

        return acteurs

    def _compile_acteurs_queryset(
        self, reparer_is_checked, selected_actions_ids, reparer_action_id
    ):
        filters = Q(statut=ActeurStatus.ACTIF)
        excludes = Q()

        if self.pas_exclusivite_reparation and reparer_is_checked:
            excludes |= Q(exclusivite_de_reprisereparation=True)

        if self.ess:
            filters &= Q(labels__code="ess")

        if self.bonus:
            filters &= Q(labels__bonus=True)

        if sous_categorie_id := self.sc_id:
            filters &= Q(
                proposition_services__sous_categories__id=sous_categorie_id,
            )

        actions_filters = Q()

        if self.label_reparacteur and reparer_is_checked:
            selected_actions_ids = [
                a for a in selected_actions_ids if a != reparer_action_id
            ]
            actions_filters |= Q(
                proposition_services__action_id=reparer_action_id,
                labels__code="reparacteur",
            )

        if selected_actions_ids:
            actions_filters |= Q(
                proposition_services__action_id__in=selected_actions_ids,
            )

        filters &= actions_filters

        return filters, excludes

    def _get_grouped_action_choices(
        self, action_displayed: list[Action]
    ) -> list[list[str]]:
        groupe_with_displayed_actions = []

        # Cast needed because of the cache
        cached_groupe_action_instances = cast(
            QuerySet[GroupeAction],
            cache.get_or_set("groupe_action_instances", get_groupe_action_instances),
        )

        for cached_groupe in cached_groupe_action_instances:
            if groupe_actions := [
                action
                # TODO : à optimiser avec le cache
                for action in cached_groupe.actions.all().order_by(  # type: ignore
                    "order"
                )
                if action in action_displayed
            ]:
                groupe_with_displayed_actions.append([cached_groupe, groupe_actions])

        grouped_action_choices = []
        for [groupe, groupe_displayed_actions] in groupe_with_displayed_actions:
            libelle = ""
            if groupe.icon:
                libelle = (
                    f'<span class="fr-px-1v qf-text-white {groupe.icon}'
                    f' fr-icon--sm qf-rounded-full qf-bg-{groupe.primary}"'
                    ' aria-hidden="true"></span>'
                )
            libelles: List[str] = []
            for gda in groupe_displayed_actions:
                if gda.libelle_groupe not in libelles:
                    libelles.append(gda.libelle_groupe)
            libelle += ", ".join(libelles).capitalize()
            code = "|".join([a.code for a in groupe_displayed_actions])
            grouped_action_choices.append([code, mark_safe(libelle)])
        return grouped_action_choices

    def _grouped_action_from(
        self, grouped_action_choices: list[list[str]], action_list: list[Action]
    ) -> list[str]:
        return [
            groupe_option[0]
            for groupe_option in grouped_action_choices
            if set(groupe_option[0].split("|")) & set([a.code for a in action_list])
        ]


class CarteSearchActeursView(ActeursListView):
    is_carte = True
    template_name = "qfdmo/carte.html"

    def setup(self, request, *args, **kwargs):
        parent_setup = super().setup(request, *args, **kwargs)

        # Action to display and check
        action_displayed = self._set_action_displayed()
        self.action_displayed = "|".join([a.code for a in action_displayed])

        action_list = self._set_action_list(action_displayed)
        self.action_list = "|".join([a.code for a in action_list])

        if self.is_carte:
            grouped_action_choices = self._get_grouped_action_choices(action_displayed)
            actions_to_select = self._get_selected_action()
            self.grouped_action = self._grouped_action_from(
                grouped_action_choices, actions_to_select
            )
            # TODO : refacto forms, merge with grouped_action field
            self.legend_grouped_action = self.grouped_action

            self.action_list = "|".join(
                [a for ga in self.grouped_action for a in ga.split("|")]
            )

        # TODO : simplifiable avec le setup
        grouped_action_choices = self._get_grouped_action_choices(
            self._set_action_displayed()
        )

        self.form = CarteForm(
            initial={
                "direction": self.direction,
                "adresse": self.adresse,
                "digital": self.digital,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "action_displayed": self.action_displayed,
                "action_list": self.action_list,
                "label_reparacteur": self.label_reparacteur,
                "epci_codes": self.epci_codes,
                "pas_exclusivite_reparation": self.pas_exclusivite_reparation,
                "bonus": self.bonus,
                "ess": self.ess,
                "bounding_box": self.bounding_box,
                "sc_id": self.sc_id,
                "grouped_action": self.grouped_action,
                "legend_grouped_action": self.legend_grouped_action,
                "sous_categorie_objet": self.sous_categorie_objet,
            }
        )

        self.form.load_choices(
            self.request,
            grouped_action_choices=grouped_action_choices,
            disable_reparer_option=(
                "reparer" not in self.form.initial.get("grouped_action", [])
            ),
        )

        return parent_setup

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, form=self.form, is_carte=True)

    def _get_selected_action_ids(self):
        return [a.id for a in self._get_selected_action()]


class FormulaireSearchActeursView(ActeursListView):
    """Affiche le formulaire utilisé sur epargnonsnosressources.gouv.fr
    Cette vue est à considérer en mode maintenance uniquement et ne doit pas être
    modifiée."""

    is_iframe = True
    template_name = "qfdmo/formulaire.html"
    form_class = FormulaireForm

    def setup(self, request, *args, **kwargs):
        parent_setup = super().setup(request, *args, **kwargs)

        # Action to display and check
        action_displayed = self._set_action_displayed()
        self.action_displayed = "|".join([a.code for a in action_displayed])

        action_list = self._set_action_list(action_displayed)
        self.action_list = "|".join([a.code for a in action_list])

        self.form = FormulaireForm(
            initial={
                "direction": self.direction,
                "adresse": self.adresse,
                "digital": self.digital,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "action_displayed": self.action_displayed,
                "action_list": self.action_list,
                "label_reparacteur": self.label_reparacteur,
                "pas_exclusivite_reparation": self.pas_exclusivite_reparation,
                "bonus": self.bonus,
                "ess": self.ess,
                "bounding_box": self.bounding_box,
                "sc_id": self.sc_id,
                "sous_categorie_objet": self.sous_categorie_objet,
            }
        )
        self.form.load_choices(self.request)

        return parent_setup

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, form=self.form, is_carte=False)

    def _get_selected_action_ids(self):
        # TODO: merge this method with the one from CarteSearchActeursView
        # and do not return a list of dict but a queryset instead
        return [a["id"] for a in self.get_action_list()]

    def get_action_list(self) -> List[dict]:
        direction = get_direction(self.request, False)
        action_displayed = self._set_action_displayed()
        actions = self._set_action_list(action_displayed)
        if direction:
            actions = [
                a for a in actions if direction in [d.code for d in a.directions.all()]
            ]
        return [model_to_dict(a, exclude=["directions"]) for a in actions]


# TODO : should be deprecated once all is moved to the displayed acteur
def getorcreate_revisionacteur(request, acteur_identifiant):
    acteur = Acteur.objects.get(identifiant_unique=acteur_identifiant)
    revision_acteur = acteur.get_or_create_revision()
    return redirect(
        "admin:qfdmo_revisionacteur_change", quote(revision_acteur.identifiant_unique)
    )


def getorcreate_correctionequipeacteur(request, acteur_identifiant):
    acteur = Acteur.objects.get(identifiant_unique=acteur_identifiant)
    revision_acteur = acteur.get_or_create_correctionequipe()
    return redirect(
        "admin:qfdmo_revisionacteur_change", quote(revision_acteur.identifiant_unique)
    )


def refresh_acteur_view(request):
    RefreshMateriazedViewThread().start()
    return redirect("admin:index")


@require_GET
def get_object_list(request):
    query = unidecode.unidecode(request.GET.get("q"))
    objets = (
        Objet.objects.annotate(
            libelle_unaccent=Unaccent(Lower("libelle")),
        )
        .prefetch_related("sous_categorie")
        .annotate(
            distance=TrigramWordDistance(query, "libelle_unaccent"),
            length=Length("libelle"),
        )
        .filter(sous_categorie__afficher=True)
        .order_by("distance", "length")[:10]
    )
    object_list = [
        {
            "label": objet.libelle,
            "sub_label": objet.sous_categorie.libelle,
            "identifier": objet.sous_categorie_id,
        }
        for objet in objets
    ]

    return JsonResponse(
        object_list,
        safe=False,
    )


def acteur_detail_redirect(request, identifiant_unique):
    displayed_acteur = DisplayedActeur.objects.get(
        identifiant_unique=identifiant_unique
    )
    return redirect("qfdmo:acteur-detail", uuid=displayed_acteur.uuid, permanent=True)


def acteur_detail(request, uuid):
    base_template = "layout/base.html"

    if request.headers.get("Turbo-Frame"):
        base_template = "layout/turbo.html"

    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    direction = request.GET.get("direction")

    displayed_acteur = DisplayedActeur.objects.prefetch_related(
        "proposition_services__sous_categories",
        "proposition_services__sous_categories__categorie",
        "proposition_services__action__groupe_action",
        "labels",
        "sources",
    ).get(uuid=uuid)

    if displayed_acteur.statut != ActeurStatus.ACTIF:
        return redirect("https://quefairedemesdechets.ademe.fr", permanent=True)

    context = {
        "base_template": base_template,
        "object": displayed_acteur,  # We can use object here so that switching
        # to a DetailView later will not required a template update
        "latitude": latitude,
        # TODO: remove when this view will be migrated to a class-based view
        "is_embedded": "carte" in request.GET or "iframe" in request.GET,
        "longitude": longitude,
        "direction": direction,
        "distance": distance_to_acteur(request, displayed_acteur),
        "display_labels_panel": bool(
            displayed_acteur.labels.filter(afficher=True, type_enseigne=False).count()
        ),
        "display_sources_panel": bool(
            displayed_acteur.sources.filter(afficher=True).count()
        ),
        "is_carte": "carte" in request.GET,
    }

    if latitude and longitude and not displayed_acteur.is_digital:
        context.update(
            itineraire_url="https://www.google.com/maps/dir/?api=1&origin="
            f"{latitude},{ longitude }"
            f"&destination={ displayed_acteur.latitude },"
            f"{ displayed_acteur.longitude }&travelMode=WALKING"
        )

    return render(request, "qfdmo/acteur.html", context)


def solution_admin(request, identifiant_unique):
    acteur = RevisionActeur.objects.filter(
        identifiant_unique=identifiant_unique
    ).first()

    if acteur:
        return redirect(
            "admin:qfdmo_revisionacteur_change", quote(acteur.identifiant_unique)
        )
    acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
    return redirect("admin:qfdmo_acteur_change", quote(acteur.identifiant_unique))
