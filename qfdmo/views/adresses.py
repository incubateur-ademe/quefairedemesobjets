import json
import logging
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
from qfdmo.forms import CarteAddressesForm, IframeAddressesForm
from qfdmo.models import (
    Acteur,
    ActeurStatus,
    ActeurType,
    Action,
    CachedDirectionAction,
    DisplayedActeur,
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
        initial["pas_exclusivite_reparation"] = self.request.GET.get(
            "pas_exclusivite_reparation", True
        )
        initial["bonus"] = self.request.GET.get("bonus")
        initial["ess"] = self.request.GET.get("ess")
        initial["bounding_box"] = self.request.GET.get("bounding_box")
        initial["sc_id"] = (
            self.request.GET.get("sc_id") if initial["sous_categorie_objet"] else None
        )

        # Action to display and check
        action_displayed = self._set_action_displayed()
        initial["action_displayed"] = "|".join([a.code for a in action_displayed])

        action_list = self._set_action_list(action_displayed)
        initial["action_list"] = "|".join([a.code for a in action_list])

        if self.request.GET.get("carte") is not None:
            grouped_action_choices = self._get_grouped_action_choices(action_displayed)
            actions_to_select = self._get_selected_action()
            initial["grouped_action"] = self._set_grouped_action(
                grouped_action_choices, actions_to_select
            )
            initial["legend_grouped_action"] = initial["grouped_action"]
            initial["action_list"] = "|".join(
                [a for ga in initial["grouped_action"] for a in ga.split("|")]
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
            grouped_action_choices = self._get_grouped_action_choices(action_displayed)

            my_form.load_choices(  # type: ignore
                self.request,
                grouped_action_choices=grouped_action_choices,
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

        # TODO : voir pour utiliser davantage le form dans cette vue
        form = self.get_form_class()(self.request.GET)
        form.is_valid()
        self.cleaned_data = form.cleaned_data

        # Manage the selection of sous_categorie_objet and actions
        acteurs = self._manage_sous_categorie_objet_and_actions()

        acteurs = acteurs.prefetch_related("action_principale")

        # Case of digital acteurs
        if self.request.GET.get("digital") and self.request.GET.get("digital") == "1":
            kwargs["acteurs"] = (
                acteurs.filter(acteur_type_id=ActeurType.get_digital_acteur_type_id())
                .annotate(min_action_order=Min("proposition_services__action__order"))
                .order_by("min_action_order", "?")
            )
            return super().get_context_data(**kwargs)

        # Case of physical acteurs
        # TODO : refactoriser ci-dessous pour passer dans
        # _manage_sous_categorie_objet_and_actions ou autre
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

    def _set_action_displayed(self) -> List[Action]:
        cached_action_instances = CachedDirectionAction.get_action_instances()
        """
        Limit to actions of the direction only in Carte mode
        """
        if direction := self.request.GET.get("direction"):
            if self.request.GET.get("carte") is not None:
                cached_action_instances = [
                    action
                    for action in cached_action_instances
                    if direction in [d.code for d in action.directions.all()]
                ]
        if action_displayed := self.request.GET.get("action_displayed", ""):
            cached_action_instances = [
                action
                for action in cached_action_instances
                if action.code in action_displayed.split("|")
            ]
        # In form mode, only display actions with afficher=True
        # TODO : discuss with epargnonsnosressources if we can remove this condition
        # or set it in get_action_instances
        if self.request.GET.get("carte") is None:
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
        if self.request.GET.get("carte") is not None:
            return [a.id for a in self._get_selected_action()]

        return [a["id"] for a in self.get_action_list()]

    def _get_reparer_action_id(self):
        """Sert essentiellement à faciliter le teste de AddressesView"""
        return CachedDirectionAction.get_reparer_action_id()

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
        elif action_list := self.cleaned_data.get("action_list"):
            # TODO : effet de bord si la list des action n'est pas cohérente avec
            # les actions affichées
            # il faut collecté les actions coché selon les groupes d'action
            codes = action_list.split("|")
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        elif action_displayed := self.cleaned_data.get("action_displayed"):
            codes = action_displayed.split("|")
        # return empty array, will search in all actions

        actions = (
            [a for a in CachedDirectionAction.get_action_instances() if a.code in codes]
            if codes
            else CachedDirectionAction.get_action_instances()
        )
        if direction := self.request.GET.get("direction"):
            actions = [
                a for a in actions if direction in [d.code for d in a.directions.all()]
            ]
        return actions

    def get_action_list(self) -> List[dict]:
        direction = get_direction(self.request)
        action_displayed = self._set_action_displayed()
        actions = self._set_action_list(action_displayed)
        if direction:
            actions = [
                a for a in actions if direction in [d.code for d in a.directions.all()]
            ]
        return [model_to_dict(a, exclude=["directions"]) for a in actions]

    def _manage_sous_categorie_objet_and_actions(self) -> QuerySet[DisplayedActeur]:
        filters, excludes = self._compile_acteurs_queryset()
        acteurs = DisplayedActeur.objects.filter(filters).exclude(excludes)
        acteurs = acteurs.prefetch_related(
            "proposition_services__sous_categories",
            "proposition_services__sous_categories__categorie",
            "proposition_services__action",
        ).distinct()

        return acteurs

    def _compile_acteurs_queryset(self):
        filters = Q(statut=ActeurStatus.ACTIF)
        excludes = Q()

        selected_actions_ids = self._get_selected_action_ids()
        reparer_action_id = self._get_reparer_action_id()
        reparer_is_checked = reparer_action_id in selected_actions_ids

        if (
            self.cleaned_data["pas_exclusivite_reparation"] is not False
            or not reparer_is_checked
        ):
            excludes |= Q(exclusivite_de_reprisereparation=True)

        if self.cleaned_data["ess"]:
            filters &= Q(labels__code="ess")

        if self.cleaned_data["bonus"]:
            filters &= Q(labels__bonus=True)

        if sous_categorie_id := self.cleaned_data.get("sc_id", 0):
            filters &= Q(
                proposition_services__sous_categories__id=sous_categorie_id,
            )

        actions_filters = Q()

        if self.cleaned_data["label_reparacteur"] and reparer_is_checked:
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
        for cached_groupe in CachedDirectionAction.get_groupe_action_instances():
            if groupe_actions := [
                action
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
                # Les classes qfdmo- ci-dessous doivent être ajoutées à la safelist
                # Tailwind dans tailwind.config.js
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
            grouped_action_choices.append([code, mark_safe(libelle)])
        return grouped_action_choices

    def _set_grouped_action(
        self, grouped_action_choices: list[list[str]], action_list: list[Action]
    ) -> list[str]:
        return [
            groupe_option[0]
            for groupe_option in grouped_action_choices
            if set(groupe_option[0].split("|")) & set([a.code for a in action_list])
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


def adresse_detail(request, identifiant_unique):
    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    direction = request.GET.get("direction")

    displayed_acteur = DisplayedActeur.objects.prefetch_related(
        "proposition_services__sous_categories",
        "proposition_services__sous_categories__categorie",
        "proposition_services__action__groupe_action",
        "labels",
        "sources",
    ).get(identifiant_unique=identifiant_unique)

    return render(
        request,
        "qfdmo/adresse_detail.html",
        {
            "adresse": displayed_acteur,
            "latitude": latitude,
            "longitude": longitude,
            "direction": direction,
            "display_labels_panel": any(
                label.afficher for label in displayed_acteur.labels.all()
            ),
            "display_sources_panel": any(
                source.afficher for source in displayed_acteur.sources.all()
            ),
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
