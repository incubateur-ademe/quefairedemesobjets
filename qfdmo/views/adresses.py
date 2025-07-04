import json
import logging
from typing import List, cast

import unidecode
from django.conf import settings
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.functions import Length, Lower
from django.db.models.query import QuerySet
from django.forms import model_to_dict
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET
from django.views.generic.edit import FormView

from core.jinja2_handler import distance_to_acteur
from core.utils import get_direction
from qfdmo.forms import FormulaireForm
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

logger = logging.getLogger(__name__)

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


def generate_google_maps_itineraire_url(
    latitude: float, longitude: float, displayed_acteur: DisplayedActeur
) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1&origin="
        f"{latitude},{longitude}"
        f"&destination={displayed_acteur.latitude},"
        f"{displayed_acteur.longitude}&travelMode=WALKING"
    )


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


class SearchActeursView(
    DigitalMixin,
    TurboFormMixin,
    FormView,
):
    # TODO : supprimer
    is_iframe = False
    is_carte = False
    is_embedded = True

    def get_initial(self):
        initial = super().get_initial()
        # TODO: refacto forms : delete this line
        initial["sous_categorie_objet"] = self.request.GET.get("sous_categorie_objet")
        # TODO: refacto forms : delete this line
        initial["adresse"] = self.request.GET.get("adresse")
        initial["digital"] = self.request.GET.get("digital", "0")
        initial["direction"] = get_direction(self.request, self.is_carte)
        # TODO: refacto forms : delete this line
        initial["latitude"] = self.request.GET.get("latitude")
        # TODO: refacto forms : delete this line
        initial["longitude"] = self.request.GET.get("longitude")
        # TODO: refacto forms : delete this line
        initial["label_reparacteur"] = self.request.GET.get("label_reparacteur")
        initial["epci_codes"] = self.request.GET.getlist("epci_codes")
        initial["pas_exclusivite_reparation"] = self.request.GET.get(
            "pas_exclusivite_reparation", True
        )
        # TODO: refacto forms : delete this line
        initial["bonus"] = self.request.GET.get("bonus")
        # TODO: refacto forms : delete this line
        initial["ess"] = self.request.GET.get("ess")
        # TODO: refacto forms : delete this line
        initial["bounding_box"] = self.request.GET.get("bounding_box")
        initial["sc_id"] = (
            self.request.GET.get("sc_id") if initial["sous_categorie_objet"] else None
        )

        # Action to display and check
        action_displayed = self._set_action_displayed()
        initial["action_displayed"] = "|".join([a.code for a in action_displayed])

        action_list = self._set_action_list(action_displayed)
        initial["action_list"] = "|".join([a.code for a in action_list])

        return initial

    def get_form(self, form_class=None):
        if self.request.GET & self.get_form_class().base_fields.keys():
            # TODO: refacto forms we should use a bounded form in this case
            # Here we check that the request shares some parameters
            # with the fields in the form. If this happens, this might
            # means that we are badly using request instead of a bounded
            # form and that we need to access a validated form.
            #
            # This case happens when the form is loaded inside a turbo-frame.
            # form = self.get_form_class()(self.request.GET)
            form = super().get_form(form_class)
        else:
            form = super().get_form(form_class)

        action_displayed = self._set_action_displayed() if self.is_carte else None
        grouped_action_choices = (
            self._get_grouped_action_choices(action_displayed)
            if action_displayed
            else None
        )

        form.load_choices(
            self.request,
            grouped_action_choices=grouped_action_choices,
            disable_reparer_option=(
                "reparer" not in form.initial.get("grouped_action", [])
            ),
        )

        return form

    def get_data_from_request_or_bounded_form(self, key: str, default=None):
        """Temporary dummy method

        There is a flaw in the way the form is instantiated, because the
        form is never bounded to its data.
        The request is directly used to perform various tasks, like
        populating some multiple choice field choices, hence missing all
        the validation provided by django forms.

        To prepare a future refactor of this form, the method here calls
        the cleaned_data when the form is bounded and the request.GET
        QueryDict when it is not bounded.
        Note : we call getlist and not get because in some cases, the request
        parameters needs to be treated as a list.

        The form is currently used for various use cases:
            - The map form
            - The "iframe form" form (for https://epargnonsnosressources.gouv.fr)
            - The turbo-frames
        The form should be bounded at least when used in turbo-frames.

        The name is explicitely very verbose because it is not meant to stay
        a long time as is.

        TODO: refacto forms : get rid of this method and use cleaned_data when
        form is valid and request.GET for non-field request parameters"""
        try:
            return self.cleaned_data.get(key, default)
        except AttributeError:
            pass

        try:
            return self.request.GET.get(key, default)
        except AttributeError:
            return self.request.GET.getlist(key, default)

    def get_context_data(self, **kwargs):
        form = self.get_form_class()(self.request.GET)

        kwargs.update(
            # TODO: refacto forms : define a BooleanField carte on CarteAddressesForm
            carte=self.is_carte,
            # TODO: refacto forms, return bounded form in template
            # form=form,
            location="{}",
        )

        if form.is_valid():
            self.cleaned_data = form.cleaned_data
        else:
            # TODO : refacto forms : handle this case properly
            self.cleaned_data = form.cleaned_data

        # Manage the selection of sous_categorie_objet and actions
        acteurs = self._acteurs_from_sous_categorie_objet_and_actions()

        if self.get_data_from_request_or_bounded_form("digital") == "1":
            acteurs = acteurs.digital()
        else:
            bbox, acteurs = self._bbox_and_acteurs_from_location_or_epci(acteurs)
            acteurs = acteurs[: self._get_max_displayed_acteurs()]

            # Set Home location (address set as input)
            # FIXME : can be manage in template using the form value ?
            if (
                latitude := self.get_data_from_request_or_bounded_form("latitude")
            ) and (
                longitude := self.get_data_from_request_or_bounded_form("longitude")
            ):
                kwargs.update(
                    location=json.dumps({"latitude": latitude, "longitude": longitude})
                )

        kwargs.update(acteurs=acteurs)
        context = super().get_context_data(**kwargs)

        # TODO : refacto forms, gérer ça autrement
        try:
            if bbox is None:
                context["form"].initial["bounding_box"] = None
        except NameError:
            pass

        return context

    def _bbox_and_acteurs_from_location_or_epci(self, acteurs):
        custom_bbox = cast(
            str, self.get_data_from_request_or_bounded_form("bounding_box")
        )
        center = center_from_leaflet_bbox(custom_bbox)
        latitude = center[1] or self.get_data_from_request_or_bounded_form("latitude")
        longitude = center[0] or self.get_data_from_request_or_bounded_form("longitude")

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

        if epci_codes := self.get_data_from_request_or_bounded_form("epci_codes"):
            geojson_list = [retrieve_epci_geojson(code) for code in epci_codes]
            bbox = bbox_from_list_of_geojson(geojson_list, buffer=0)
            if geojson_list:
                acteurs = acteurs.in_geojson(
                    [json.dumps(geojson) for geojson in geojson_list]
                )
            return compile_leaflet_bbox(bbox), acteurs

        return custom_bbox, acteurs.none()

    def _get_max_displayed_acteurs(self):
        if self.request.GET.get("limit", "").isnumeric():
            return int(self.request.GET.get("limit"))
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
        if action_displayed := self.get_data_from_request_or_bounded_form(
            "action_displayed", ""
        ):
            cached_action_instances = [
                action
                for action in cached_action_instances
                if action.code in action_displayed.split("|")
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
        if action_list := self.get_data_from_request_or_bounded_form("action_list", ""):
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
        if self.get_data_from_request_or_bounded_form("grouped_action"):
            return [
                code
                for new_groupe_action in self.get_data_from_request_or_bounded_form(
                    "grouped_action"
                )
                for code in new_groupe_action.split("|")
            ]
        # Selection is not set in interface, get all available from
        # (checked_)action_list
        if self.get_data_from_request_or_bounded_form("action_list"):
            return self.get_data_from_request_or_bounded_form("action_list", "").split(
                "|"
            )
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        if self.get_data_from_request_or_bounded_form("action_displayed"):
            return self.get_data_from_request_or_bounded_form(
                "action_displayed", ""
            ).split("|")
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

        acteurs = DisplayedActeur.objects.filter(filters).exclude(excludes)

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

        if (
            self.get_data_from_request_or_bounded_form("pas_exclusivite_reparation")
            is not False
            or not reparer_is_checked
        ):
            excludes |= Q(exclusivite_de_reprisereparation=True)

        if self.get_data_from_request_or_bounded_form("ess"):
            filters &= Q(labels__code="ess")

        if self.get_data_from_request_or_bounded_form("bonus"):
            filters &= Q(labels__bonus=True)

        if sous_categorie_id := self.get_data_from_request_or_bounded_form("sc_id", 0):
            filters &= Q(
                proposition_services__sous_categories__id=sous_categorie_id,
            )

        actions_filters = Q()

        if (
            self.get_data_from_request_or_bounded_form("label_reparacteur")
            and reparer_is_checked
        ):
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

    def get_cached_groupe_action_with_displayed_actions(self, action_displayed):
        # Cast needed because of the cache
        cached_groupe_action_instances = cast(
            QuerySet[GroupeAction],
            cache.get_or_set("groupe_action_instances", get_groupe_action_instances),
        )

        # Fetch actions from cache only if they are displayed
        # for the end user
        cached_groupe_action_with_displayed_actions = []
        for cached_groupe in cached_groupe_action_instances:
            if displayed_actions_from_groupe_actions := [
                action
                # TODO : à optimiser avec le cache
                for action in cached_groupe.actions.all().order_by(  # type: ignore
                    "order"
                )
                if action in action_displayed
            ]:
                cached_groupe_action_with_displayed_actions.append(
                    [cached_groupe, displayed_actions_from_groupe_actions]
                )
        return cached_groupe_action_with_displayed_actions

    def _get_grouped_action_choices(
        self, action_displayed: list[Action]
    ) -> list[list[str]]:
        """Generate a list of choices for form field
        used in legend"""
        # Generate a tuple of (code, libelle) used in the frontend.
        # The libelle is automatically picked up by django templating
        # when generating the form.
        grouped_action_choices = []
        for [
            groupe,
            groupe_displayed_actions,
        ] in self.get_cached_groupe_action_with_displayed_actions(action_displayed):
            libelle = ""
            if groupe.icon:
                libelle = render_to_string(
                    "forms/widgets/groupe_action_label.html",
                    {
                        "groupe_action": groupe,
                        "libelle": groupe.get_libelle_from(groupe_displayed_actions),
                    },
                )

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


class FormulaireSearchActeursView(SearchActeursView):
    """Affiche le formulaire utilisé sur epargnonsnosressources.gouv.fr
    Cette vue est à considérer en mode maintenance uniquement et ne doit pas être
    modifiée."""

    is_iframe = True
    template_name = "qfdmo/formulaire.html"
    form_class = FormulaireForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(map_container_id="formulaire")
        return context

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


def getorcreate_revisionacteur(request, acteur_identifiant):
    try:
        acteur = Acteur.objects.get(identifiant_unique=acteur_identifiant)
        revision_acteur = acteur.get_or_create_revision()
    except Acteur.DoesNotExist as e:
        # Case of Parent Acteur
        revision_acteur = RevisionActeur.objects.get(
            identifiant_unique=acteur_identifiant
        )
        if not revision_acteur.is_parent:
            raise e
    return redirect(revision_acteur.change_url)


@require_GET
def get_object_list(request):
    query = request.GET.get("q")
    if not query:
        return JsonResponse([], safe=False)

    query = unidecode.unidecode(query)
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


def _get_acteur_or_parent(**query_kwargs) -> DisplayedActeur | None:
    try:
        return DisplayedActeur.objects.get(**query_kwargs)
    except DisplayedActeur.DoesNotExist:
        revision_acteur = RevisionActeur.objects.get(**query_kwargs)
        return DisplayedActeur.objects.get(identifiant_unique=revision_acteur.parent_id)


def acteur_detail_redirect(request, identifiant_unique):
    try:
        displayed_acteur = _get_acteur_or_parent(identifiant_unique=identifiant_unique)
    except ObjectDoesNotExist:
        raise Http404("L'adresse que vous cherchez n'existe plus")

    return redirect("qfdmo:acteur-detail", uuid=displayed_acteur.uuid, permanent=True)


def acteur_detail(request, uuid):
    base_template = "layout/base.html"

    if request.headers.get("Turbo-Frame"):
        base_template = "layout/turbo.html"

    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    direction = request.GET.get("direction")

    try:
        displayed_acteur = DisplayedActeur.objects.prefetch_related(
            "proposition_services__sous_categories",
            "proposition_services__sous_categories__categorie",
            "proposition_services__action__groupe_action",
            "labels",
            "sources",
        ).get(uuid=uuid)
    except DisplayedActeur.DoesNotExist:
        # FIXME: it is impossible to get check if the revisionacteur has a parent
        # because the revision_acteur doesn't have any UUID
        # to resolve it we need compute uuid on revisionacteur layer
        raise Http404("L'adresse que vous cherchez n'existe plus")

    # FIXME: This case shouldn't occure because we compute only active displayed
    # acteurs in dislayedacteur table
    if displayed_acteur is None or displayed_acteur.statut != ActeurStatus.ACTIF:
        return redirect(settings.ASSISTANT["BASE_URL"], permanent=True)

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
        "map_container_id": request.GET.get("map_container_id", "carte"),
    }

    if latitude and longitude and not displayed_acteur.is_digital:
        context.update(
            itineraire_url=generate_google_maps_itineraire_url(
                latitude, longitude, displayed_acteur
            )
        )

    return render(request, "qfdmo/acteur.html", context)


def solution_admin(request, identifiant_unique):
    revision_acteur = RevisionActeur.objects.filter(
        identifiant_unique=identifiant_unique
    ).first()

    if revision_acteur:
        return redirect(revision_acteur.change_url)
    acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
    return redirect(acteur.change_url)
