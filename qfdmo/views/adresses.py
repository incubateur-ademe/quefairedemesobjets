import json
import logging
from html import escape
from typing import List

import unidecode
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance  # type: ignore
from django.db.models import Min, Q
from django.db.models.functions import Length, Lower
from django.db.models.query import QuerySet
from django.forms import model_to_dict
from django.forms.forms import BaseForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET
from django.views.generic.edit import FormView

from core.utils import get_direction
from qfdmo.forms import CarteAddressesForm, ConfiguratorForm, IframeAddressesForm
from qfdmo.models import (
    Acteur,
    ActeurStatus,
    ActeurType,
    CachedDirectionAction,
    DisplayedActeur,
    DisplayedPropositionService,
    Objet,
    RevisionActeur,
)
from qfdmo.thread.materialized_view import RefreshMateriazedViewThread

logger = logging.getLogger(__name__)

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


class AddressesView(FormView):
    form_class = IframeAddressesForm
    template_name = "qfdmo/adresses.html"

    def get_form_class(self) -> type:
        if self.request.GET.get("carte") is not None:
            return CarteAddressesForm
        return super().get_form_class()

    def get_initial(self):
        initial = super().get_initial()
        initial["sous_categorie_objet"] = self.request.GET.get("sous_categorie_objet")
        initial["adresse"] = self.request.GET.get("adresse")
        initial["digital"] = self.request.GET.get("digital", "0")
        initial["direction"] = get_direction(self.request)
        initial["latitude"] = self.request.GET.get("latitude")
        initial["longitude"] = self.request.GET.get("longitude")
        initial["label_reparacteur"] = self.request.GET.get("label_reparacteur")
        initial["bonus"] = self.request.GET.get("bonus")
        initial["ess"] = self.request.GET.get("ess")
        initial["bounding_box"] = self.request.GET.get("bounding_box")
        initial["sc_id"] = (
            self.request.GET.get("sc_id") if initial["sous_categorie_objet"] else None
        )

        # Action to display and check
        action_displayed = self._set_action_displayed()
        initial["action_displayed"] = "|".join(action_displayed)
        action_list = self._set_action_list(action_displayed)
        initial["action_list"] = "|".join(action_list)
        if self.request.GET.get("carte") is not None:
            groupe_options = self._get_groupe_options(action_displayed)
            initial["grouped_action"] = self._set_grouped_action(
                groupe_options, action_list
            )

        return initial

    def get_form(self, form_class: type | None = None) -> BaseForm:
        if form_class is None:
            form_class = self.get_form_class()
        my_form = super().get_form(form_class)
        # Here we need to load choices after initialisation because of async management
        # in prod + cache

        if form_class == CarteAddressesForm:
            action_displayed = self._set_action_displayed()
            groupe_options = self._get_groupe_options(action_displayed)

            my_form.load_choices(  # type: ignore
                self.request,
                groupe_options=groupe_options,
                disable_reparer_option=(
                    "reparer" not in my_form.initial["grouped_action"]
                ),
            )
        else:
            my_form.load_choices(self.request)  # type: ignore
        return my_form

    def get_context_data(self, **kwargs):
        kwargs["location"] = "{}"
        kwargs["carte"] = self.request.GET.get("carte") is not None

        # Manage the selection of sous_categorie_objet and actions
        acteurs = self._manage_sous_categorie_objet_and_actions()

        if self.request.GET.get("ess"):
            acteurs = acteurs.filter(labels__code="ess")

        if self.request.GET.get("bonus"):
            acteurs = acteurs.filter(labels__bonus=True)

        # Case of digital acteurs
        if self.request.GET.get("digital") and self.request.GET.get("digital") == "1":
            kwargs["acteurs"] = (
                acteurs.filter(acteur_type_id=ActeurType.get_digital_acteur_type_id())
                .annotate(min_action_order=Min("proposition_services__action__order"))
                .order_by("min_action_order", "?")
            )
            return super().get_context_data(**kwargs)

        # Case of physical acteurs
        else:
            # Exclude digital acteurs
            acteurs = acteurs.exclude(
                acteur_type_id=ActeurType.get_digital_acteur_type_id()
            )

            # Set Home location (address set as input)
            # FIXME : can be manage in template using the form value ?
            if (latitude := self.request.GET.get("latitude", None)) and (
                longitude := self.request.GET.get("longitude", None)
            ):
                kwargs["location"] = json.dumps(
                    {"latitude": latitude, "longitude": longitude}
                )

            # Manage bounding_box parameter
            center, my_bounding_box_polygon = self._get_search_in_zone_params()

            # With bounding_box parameter
            if my_bounding_box_polygon:
                if center:
                    longitude = center[0]
                    latitude = center[1]

                bounding_box_acteurs = acteurs.filter(
                    location__within=Polygon.from_bbox(my_bounding_box_polygon)
                ).order_by("?")
                bounding_box_acteurs = bounding_box_acteurs[
                    : self._get_max_displayed_acteurs()
                ]
                if bounding_box_acteurs.count() > 0:
                    kwargs["bounding_box"] = my_bounding_box_polygon
                    kwargs["acteurs"] = bounding_box_acteurs
                    return super().get_context_data(**kwargs)

            # if not bounding_box or if no acteur in the bounding_box
            if latitude and longitude:
                reference_point = Point(float(longitude), float(latitude), srid=4326)
                distance_in_degrees = settings.DISTANCE_MAX / 111320

                kwargs["acteurs"] = (
                    acteurs.annotate(distance=Distance("location", reference_point))
                    .filter(
                        location__dwithin=(
                            reference_point,
                            distance_in_degrees,
                        )
                    )
                    .order_by("distance")[: self._get_max_displayed_acteurs()]
                )

                # Remove bounding_box parameter
                context = super().get_context_data(**kwargs)
                if kwargs["acteurs"]:
                    context["form"].initial["bounding_box"] = None
                return context

        kwargs["acteurs"] = DisplayedActeur.objects.none()
        return super().get_context_data(**kwargs)

    def _get_max_displayed_acteurs(self):
        if self.request.GET.get("limit", "").isnumeric():
            return int(self.request.GET.get("limit"))
        if self.request.GET.get("carte") is not None:
            return settings.CARTE_MAX_SOLUTION_DISPLAYED
        return settings.DEFAULT_MAX_SOLUTION_DISPLAYED

    def _get_search_in_zone_params(self):
        center = []
        my_bounding_box_polygon = []
        if search_in_zone := self.request.GET.get("bounding_box"):
            try:
                search_in_zone = json.loads(search_in_zone)
            except json.JSONDecodeError:
                logger.error("Error while parsing bounding_box parameter")
                return center, my_bounding_box_polygon

            if (
                "center" in search_in_zone
                and "lat" in search_in_zone["center"]
                and "lng" in search_in_zone["center"]
            ):
                center = [
                    search_in_zone["center"]["lng"],
                    search_in_zone["center"]["lat"],
                ]

            if (
                "southWest" in search_in_zone
                and "lat" in search_in_zone["southWest"]
                and "lng" in search_in_zone["southWest"]
                and "northEast" in search_in_zone
                and "lat" in search_in_zone["northEast"]
                and "lng" in search_in_zone["northEast"]
            ):
                my_bounding_box_polygon = [
                    search_in_zone["southWest"]["lng"],
                    search_in_zone["southWest"]["lat"],
                    search_in_zone["northEast"]["lng"],
                    search_in_zone["northEast"]["lat"],
                ]  # [xmin, ymin, xmax, ymax]
        return center, my_bounding_box_polygon

    def _set_action_displayed(self) -> list[str]:
        cached_action_instances = CachedDirectionAction.get_action_instances()
        if self.request.GET.get("carte") is None:
            cached_action_instances = [
                action
                for action in CachedDirectionAction.get_action_instances()
                if action.afficher
            ]
        if action_displayed := self.request.GET.get("action_displayed", ""):
            return [
                action.code
                for action in cached_action_instances
                if action.code in action_displayed.split("|")
            ]
        return [action.code for action in cached_action_instances]

    def _set_action_list(self, action_displayed):
        if action_list := self.request.GET.get("action_list", ""):
            return [
                action.code
                for action in CachedDirectionAction.get_action_instances()
                if action.code in action_list.split("|")
                and action.code in action_displayed
            ]
        return action_displayed

    def _get_selected_action_code(self):
        """
        Get the action to include in the request
        """
        # FIXME : est-ce possible d'optimiser en accédant au valeur initial du form ?

        # selection from interface
        if self.request.GET.get("grouped_action"):
            return [
                code
                for new_groupe_action in self.request.GET.getlist("grouped_action")
                for code in new_groupe_action.split("|")
            ]
        # Selection is not set in interface, get all available from
        # (checked_)action_list
        if self.request.GET.get("action_list"):
            return self.request.GET.get("action_list", "").split("|")
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        if self.request.GET.get("action_displayed"):
            return self.request.GET.get("action_displayed", "").split("|")
        # return empty array, will search in all actions
        return []

    def _get_selected_action_ids(self):
        """
        Get the action to include in the request
        """
        # FIXME : est-ce possible d'optimiser en accédant au valeur initial du form ?
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
        if self.request.GET.get("action_list"):
            codes = self.request.GET.get("action_list", "").split("|")
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        if self.request.GET.get("action_displayed"):
            codes = self.request.GET.get("action_displayed", "").split("|")
        # return empty array, will search in all actions
        return (
            [
                a.id
                for a in CachedDirectionAction.get_action_instances()
                if a.code in codes
            ]
            if codes
            else []
        )

    def get_action_list(self) -> List[dict]:
        direction = get_direction(self.request)
        action_displayed = self._set_action_displayed()
        action_list = self._set_action_list(action_displayed)
        actions = [
            a
            for a in CachedDirectionAction.get_action_instances()
            if a.code in action_list
        ]
        if direction:
            actions = [
                a for a in actions if direction in [d.code for d in a.directions.all()]
            ]
        return [model_to_dict(a, exclude=["directions"]) for a in actions]

    def _manage_sous_categorie_objet_and_actions(self) -> QuerySet[DisplayedActeur]:
        sous_categorie_id = None
        if (
            self.request.GET.get("sous_categorie_objet")
            and self.request.GET.get("sc_id", "").isnumeric()
        ):
            sous_categorie_id = int(self.request.GET.get("sc_id", "0"))

        action_selection_ids = (
            self._get_selected_action_ids()
            if self.request.GET.get("carte") is not None
            else [a["id"] for a in self.get_action_list()]
        )

        ps_filter = self._build_ps_filter(action_selection_ids, sous_categorie_id)

        acteurs = DisplayedActeur.objects.filter(ps_filter)

        acteurs = acteurs.prefetch_related(
            "proposition_services__sous_categories",
            "proposition_services__sous_categories__categorie",
            "proposition_services__action",
            "proposition_services__acteur_service",
        ).distinct()

        if sous_categorie_id:
            acteurs = acteurs.filter(
                proposition_services__sous_categories__id=sous_categorie_id
            )

        return acteurs

    def _build_ps_filter(self, action_selection_ids, sous_categorie_id: int | None):
        reparer_action_id = None
        if (
            self.request.GET.get("label_reparacteur")
            and CachedDirectionAction.get_reparer_action_id() in action_selection_ids
        ):
            reparer_action_id = CachedDirectionAction.get_reparer_action_id()
            action_selection_ids = [
                a for a in action_selection_ids if a != reparer_action_id
            ]

        ps_filter = Q()
        if sous_categorie_id:
            if action_selection_ids:
                ps_filter = ps_filter | Q(
                    proposition_services__in=DisplayedPropositionService.objects.filter(
                        action_id__in=action_selection_ids,
                        sous_categories__id=sous_categorie_id,
                    ),
                    statut=ActeurStatus.ACTIF,
                )
            if reparer_action_id:
                ps_filter = ps_filter | Q(
                    proposition_services__in=DisplayedPropositionService.objects.filter(
                        action_id=reparer_action_id,
                        sous_categories__id=sous_categorie_id,
                    ),
                    labels__code="reparacteur",
                    statut=ActeurStatus.ACTIF,
                )
        else:
            if action_selection_ids:
                ps_filter = ps_filter | Q(
                    proposition_services__action_id__in=action_selection_ids,
                    statut=ActeurStatus.ACTIF,
                )
            if reparer_action_id:
                ps_filter = ps_filter | Q(
                    proposition_services__action_id=reparer_action_id,
                    labels__code="reparacteur",
                    statut=ActeurStatus.ACTIF,
                )
        return ps_filter

    def _get_groupe_options(self, action_displayed: list[str]) -> list[list[str]]:
        groupe_with_displayed_actions = []
        for cached_groupe in CachedDirectionAction.get_groupe_action_instances():
            if groupe_actions := [
                action
                for action in cached_groupe.actions.all().order_by(  # type: ignore
                    "order"
                )
                if action.code in action_displayed
            ]:
                groupe_with_displayed_actions.append([cached_groupe, groupe_actions])

        groupe_options = []
        for [groupe, groupe_displayed_actions] in groupe_with_displayed_actions:
            libelle = ""
            if groupe.icon:
                libelle = (
                    f'<span class="fr-px-1v qfdmo-text-white {groupe.icon}'
                    f' fr-icon--sm qfdmo-rounded-full qfdmo-bg-{groupe.couleur}"'
                    ' aria-hidden="true"></span>&nbsp;'
                )
            libelles: List[str] = []
            for gda in groupe_displayed_actions:
                if gda.libelle_groupe not in libelles:
                    libelles.append(gda.libelle_groupe)
            libelle += ", ".join(libelles).capitalize()
            code = "|".join([a.code for a in groupe_displayed_actions])
            groupe_options.append([code, mark_safe(libelle)])
        return groupe_options

    def _set_grouped_action(
        self, groupe_options: list[list[str]], action_list: list[str]
    ) -> list[str]:
        return [
            groupe_option[0]
            for groupe_option in groupe_options
            if set(groupe_option[0].split("|")) & set(action_list)
        ]


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


def adresse_detail(request, identifiant_unique):
    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    direction = request.GET.get("direction")

    displayed_acteur = DisplayedActeur.objects.prefetch_related(
        "proposition_services__sous_categories",
        "proposition_services__sous_categories__categorie",
        "proposition_services__action",
        "proposition_services__acteur_service",
        "labels",
        "source",
    ).get(identifiant_unique=identifiant_unique)

    return render(
        request,
        "qfdmo/adresse_detail.html",
        {
            "adresse": displayed_acteur,
            "latitude": latitude,
            "longitude": longitude,
            "direction": direction,
        },
    )


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


class ConfiguratorView(FormView):
    form_class = ConfiguratorForm
    template_name = "qfdmo/iframe_configurator.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["limit"] = self.request.GET.get("limit")
        initial["address_placeholder"] = self.request.GET.get("address_placeholder")
        initial["iframe_mode"] = self.request.GET.get("iframe_mode")
        initial["direction"] = self.request.GET.get("direction")
        initial["first_dir"] = self.request.GET.get("first_dir")
        initial["action_displayed"] = self.request.GET.getlist(
            "action_displayed",
        )
        initial["action_list"] = self.request.GET.getlist(
            "action_list",
        )
        initial["max_width"] = self.request.GET.get("max_width")
        initial["height"] = self.request.GET.get("height")
        initial["iframe_attributes"] = self.request.GET.get("iframe_attributes")
        initial["bounding_box"] = self.request.GET.get("bounding_box")
        return initial

    def get_context_data(self, **kwargs):
        # TODO : clean up input to avoid security issues
        iframe_mode = self.request.GET.get("iframe_mode")

        iframe_host = (
            "http"
            + ("s" if self.request.is_secure() else "")
            + "://"
            + self.request.get_host()
        )

        iframe_url = None
        if iframe_mode == "carte":
            iframe_url = iframe_host + "/static/carte.js"
        if iframe_mode == "form":
            iframe_url = iframe_host + "/static/iframe.js"

        attributes = {}

        if first_dir := self.request.GET.get("first_dir"):
            attributes["first_dir"] = escape(first_dir.replace("first_", ""))

        for key in [
            "direction",
            "max_width",
            "height",
            "limit",
            "address_placeholder",
        ]:
            if value := self.request.GET.get(key):
                attributes[key] = escape(value)

        for key in ["action_displayed", "action_list"]:
            if value := self.request.GET.getlist(key):
                attributes[key] = escape("|".join(value))

        for key in ["iframe_attributes", "bounding_box"]:
            if value := self.request.GET.get(key):
                try:
                    attributes[key] = json.dumps(
                        json.loads(value.replace("\r\n", "").replace("\n", ""))
                    )
                except json.JSONDecodeError:
                    attributes[key] = ""

        if iframe_url:
            kwargs["iframe_script"] = f"<script src='{ iframe_url }'"
            for key, value in attributes.items():
                kwargs["iframe_script"] += f" data-{key}='{value}'"
            kwargs["iframe_script"] += "></script>"

        return super().get_context_data(**kwargs)
