import json
import logging
from abc import ABC, abstractmethod
from typing import cast

import unidecode
from django.conf import settings
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import (
    Exists,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce, Length, Lower
from django.db.models.query import QuerySet
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from django.views.generic.edit import FormView
from wagtail.query import Any

from qfdmd.models import Synonyme
from qfdmo.geo_api import bbox_from_list_of_geojson, retrieve_epci_geojson
from qfdmo.map_utils import (
    center_from_frontend_bbox,
    compile_frontend_bbox,
    sanitize_frontend_bbox,
)
from qfdmo.models import Acteur, ActeurStatus, DisplayedActeur, RevisionActeur
from qfdmo.models.acteur import DisplayedPropositionService, LabelQualite
from qfdmo.models.action import (
    GroupeAction,
    get_reparer_action_id,
)

logger = logging.getLogger(__name__)

BAN_API_URL = "https://data.geopf.fr/geocodage/search/?q={}"


def generate_google_maps_itineraire_url(
    latitude: float, longitude: float, displayed_acteur: DisplayedActeur
) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1&origin="
        f"{latitude},{longitude}"
        f"&destination={displayed_acteur.latitude},"
        f"{displayed_acteur.longitude}&travelMode=WALKING"
    )


class TurboFormMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.turbo = request.headers.get("Turbo-Frame")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.turbo:
            context.update(turbo=True, base_template="ui/layout/turbo.html")
        else:
            context.update(base_template="ui/layout/base.html")

        return context


class SearchActeursView(
    ABC,
    TurboFormMixin,
    FormView,
):
    @abstractmethod
    def _get_direction(self):
        pass

    @abstractmethod
    def _get_max_displayed_acteurs(self) -> int:
        pass

    @abstractmethod
    def _get_action_ids(self) -> list[str]:
        pass

    @abstractmethod
    def _get_ess(self) -> bool:
        pass

    @abstractmethod
    def _get_label_reparacteur(self) -> bool:
        pass

    @abstractmethod
    def _get_bonus(self) -> bool:
        pass

    @abstractmethod
    def _get_sous_categorie_ids(self) -> list[int]:
        pass

    def _get_distance_max(self):
        """The distance after which we stop displaying acteurs on the first request"""
        return settings.DISTANCE_MAX

    # TODO : supprimer
    is_iframe = False
    is_carte = False
    is_embedded = True
    paginate = False

    def get_initial(self):
        initial = super().get_initial()
        # TODO: refacto forms : delete this line
        initial["adresse"] = self.request.GET.get("adresse")
        # TODO: refacto forms : delete this line
        initial["latitude"] = self.request.GET.get("latitude")
        # TODO: refacto forms : delete this line
        initial["longitude"] = self.request.GET.get("longitude")
        initial["epci_codes"] = self.request.GET.getlist("epci_codes")

        # TODO: refacto forms : delete this line
        initial["bounding_box"] = self.request.GET.get("bounding_box")
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
            carte=self.is_carte,
        )

        if form.is_valid():
            self.cleaned_data = form.cleaned_data
        else:
            # TODO : refacto forms : handle this case properly
            self.cleaned_data = form.cleaned_data

        # Manage the selection of sous_categorie_objet and actions
        acteurs = self._build_acteurs_queryset_from_sous_categorie_objet_and_actions()
        bbox, acteurs = self._build_acteurs_queryset_from_location(acteurs, **kwargs)

        # After enriching acteurs
        acteurs = self._enrich_acteurs_queryset_with_icons(acteurs)

        # Prefetch ALL GroupeActions (typically small dataset)
        # This allows us to access any GroupeAction by ID without additional queries
        all_groupe_actions = {ga.id: ga for ga in GroupeAction.objects.all()}
        if self.paginate:
            page_size = 10
            paginated_acteurs = Paginator(
                acteurs,
                page_size,
            )
            paginated_acteurs_obj = paginated_acteurs.page(
                self.request.GET.get("page", 1)
            )
            kwargs.update(
                paginated_acteurs_obj=paginated_acteurs_obj,
                count=paginated_acteurs.count,
            )
        else:
            kwargs.update(acteurs=acteurs)

        context = super().get_context_data(**kwargs)

        context.update(
            location=getattr(self, "location", ""),
            all_groupe_actions=all_groupe_actions,
            sous_categories_ids=self.sous_categorie_ids,
            selected_actions_ids=self.selected_action_ids,
        )

        # TODO : refacto forms, gérer ça autrement
        try:
            if bbox is None:
                context["form"].initial["bounding_box"] = None
        except NameError:
            pass

        return context

    def _build_acteurs_queryset_from_location(
        self, acteurs: QuerySet[DisplayedActeur], **kwargs
    ) -> tuple[Any, QuerySet[DisplayedActeur]]:
        """
        Handle the scoped acteurs following the order of priority:
        - bbox
        - epci_codes
        - user location
        """
        # Get filter criteria from form
        self.selected_action_ids = self._get_action_ids()
        self.sous_categorie_ids = self._get_sous_categorie_ids()

        acteurs = (
            acteurs.select_related(
                "action_principale",
                "action_principale__groupe_action",
            )
            .prefetch_related(
                Prefetch(
                    "proposition_services",
                    queryset=DisplayedPropositionService.objects.filter(
                        action_id__in=self.selected_action_ids,
                        sous_categories__id__in=self.sous_categorie_ids,
                    )
                    .select_related(
                        "action",
                        "action__groupe_action",
                    )
                    .prefetch_related(
                        "sous_categories",
                        "sous_categories__categorie",
                    )
                    .distinct(),
                ),
                Prefetch(
                    "labels",
                    queryset=LabelQualite.objects.all(),
                ),
            )
            .annotate(
                is_bonus_reparation=Exists(
                    LabelQualite.objects.filter(  # Replace with your actual Label model
                        acteur=OuterRef("pk"), afficher=True, bonus=True
                    )
                )
            )
        )

        bbox, acteurs = self._bbox_and_acteurs_from_location_or_epci(acteurs)

        acteurs = acteurs.only(
            "location",
            "identifiant_unique",
            "action_principale_id",
            "uuid",
        )

        if getattr(acteurs, "_has_distance_field", False):
            acteurs = acteurs.distinct("distance")
        else:
            acteurs = acteurs.distinct()

        acteurs = acteurs[: self._get_max_displayed_acteurs()]

        if getattr(acteurs, "_needs_reparer_bonus", False):
            acteurs = acteurs.with_bonus().with_reparer()

        return bbox, acteurs

    def _bbox_and_acteurs_from_location_or_epci(self, acteurs):
        custom_bbox = cast(
            str, self.get_data_from_request_or_bounded_form("bounding_box")
        )
        center = center_from_frontend_bbox(custom_bbox)
        latitude = center[1] or self.get_data_from_request_or_bounded_form("latitude")
        longitude = center[0] or self.get_data_from_request_or_bounded_form("longitude")

        # Store for later assignation in get_context_data
        if latitude and longitude:
            self.location = json.dumps({"latitude": latitude, "longitude": longitude})

        # A BBOX was set in the Configurateur OR the user interacted with
        # the map, that set a bounding box in its browser.
        if custom_bbox:
            bbox = sanitize_frontend_bbox(custom_bbox)
            acteurs_in_bbox = acteurs.in_bbox(bbox)

            if acteurs_in_bbox.exists():
                return custom_bbox, acteurs_in_bbox

        # At the beginning, there is no bounding box.
        # Hence, we query the Acteurs from a center point.
        if latitude and longitude:
            acteurs_from_center = acteurs.from_center(
                longitude, latitude, self._get_distance_max()
            )
            if acteurs_from_center.exists():
                custom_bbox = None

            return custom_bbox, acteurs_from_center

        if epci_codes := self.get_data_from_request_or_bounded_form("epci_codes"):
            geojson_list = [retrieve_epci_geojson(code) for code in epci_codes]
            bbox = bbox_from_list_of_geojson(geojson_list, buffer=0)
            if geojson_list:
                acteurs = acteurs.in_geojson(
                    [json.dumps(geojson) for geojson in geojson_list]
                )
            return compile_frontend_bbox(bbox), acteurs

        return custom_bbox, acteurs.none()

    def _build_acteurs_queryset_from_sous_categorie_objet_and_actions(
        self,
    ) -> QuerySet[DisplayedActeur]:
        selected_actions_ids = self._get_action_ids()
        reparer_action_id = cache.get_or_set("reparer_action_id", get_reparer_action_id)
        reparer_is_checked = reparer_action_id in selected_actions_ids
        filters, excludes = self._compile_acteurs_queryset(
            reparer_is_checked, selected_actions_ids, reparer_action_id
        )

        acteurs = DisplayedActeur.objects.filter(filters).exclude(excludes)

        # Store whether we need reparer/bonus annotations for later
        # We'll apply them AFTER limiting to avoid expensive subqueries on all rows
        acteurs._needs_reparer_bonus = reparer_is_checked

        return acteurs

    def _enrich_acteurs_queryset_with_icons(
        self, acteurs: QuerySet[DisplayedActeur]
    ) -> QuerySet[DisplayedActeur]:
        default_groupe_action_id = cache.get_or_set(
            "default_groupe_action_id",
            lambda: GroupeAction.objects.order_by("order")
            .values_list("id", flat=True)
            .first(),
            timeout=3600,
        )

        matching_proposition_services = DisplayedPropositionService.objects.filter(
            acteur_id=OuterRef("pk"),
        )
        if self.selected_action_ids:
            matching_proposition_services = matching_proposition_services.filter(
                action_id__in=self.selected_action_ids,
            )
        if self.sous_categorie_ids:
            matching_proposition_services = matching_proposition_services.filter(
                sous_categories__id__in=self.sous_categorie_ids,
            )

        principal_ga_subquery = matching_proposition_services.filter(
            action_id=OuterRef("action_principale_id"),
        ).values("action__groupe_action_id")[:1]
        fallback_ga_subquery = matching_proposition_services.order_by(
            "action__groupe_action__order",
            "action__order",
            "pk",
        ).values("action__groupe_action_id")[:1]

        acteurs = acteurs.annotate(
            computed_groupe_action_id=Coalesce(
                Subquery(principal_ga_subquery),
                Subquery(fallback_ga_subquery),
                Value(default_groupe_action_id),
                output_field=IntegerField(),
            ),
        )

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

        if self._get_ess():
            filters &= Q(labels__code="ess")

        if self._get_bonus():
            filters &= Q(labels__bonus=True)

        if sous_categorie_ids := self._get_sous_categorie_ids():
            filters &= Q(
                proposition_services__sous_categories__id__in=sous_categorie_ids,
            )

        actions_filters = Q()

        if self._get_label_reparacteur() and reparer_is_checked:
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
def get_synonyme_list(request):
    query = request.GET.get("q")
    only_reemploi = bool(request.GET.get("only_reemploi"))

    if not query:
        return JsonResponse([], safe=False)

    query = unidecode.unidecode(query)
    # FIXME : reemploi_possible = True should be only user for formulaire
    # else we just need to be sure that a sous_categorie_objet is linked to the synonyme
    # via produit
    # FIXME : we get the first sous_categorie_objet of the synonyme but we should get
    # all sous_categorie_objets of the synonyme and manage multi-sous_categorie_objets
    synonymes = (
        Synonyme.objects.annotate(
            nom_unaccent=Unaccent(Lower("nom")),
        )
        .prefetch_related("produit__sous_categories")
        .annotate(
            distance=TrigramWordDistance(query, "nom_unaccent"),
            length=Length("nom"),
        )
        .filter(produit__sous_categories__id__isnull=False)
        .order_by("distance", "length")
    )
    if only_reemploi:
        synonymes = synonymes.filter(produit__sous_categories__reemploi_possible=True)
    synonymes = synonymes.distinct()[:10]

    synonyme_list = []
    for synonyme in synonymes:
        if premiere_sous_categorie := synonyme.produit.sous_categories.first():
            synonyme_list.append(
                {
                    "label": synonyme.nom,
                    "sub_label": premiere_sous_categorie.libelle,
                    "identifier": premiere_sous_categorie.id,
                }
            )

    return JsonResponse(
        synonyme_list,
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
    base_template = "ui/layout/base.html"

    if request.headers.get("Turbo-Frame"):
        base_template = "ui/layout/turbo.html"

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
        return redirect(settings.BASE_URL, permanent=True)

    # Use prefetched data to avoid additional queries
    display_labels_panel = any(
        label.afficher and not label.type_enseigne
        for label in displayed_acteur.labels.all()
    )
    display_sources_panel = any(
        source.afficher for source in displayed_acteur.sources.all()
    )

    context = {
        "base_template": base_template,
        "object": displayed_acteur,  # We can use object here so that switching
        # to a DetailView later will not required a template update
        "latitude": latitude,
        # TODO: remove when this view will be migrated to a class-based view
        "is_embedded": "carte" in request.GET or "iframe" in request.GET,
        "longitude": longitude,
        "direction": direction,
        "display_labels_panel": display_labels_panel,
        "display_sources_panel": display_sources_panel,
        "is_carte": "carte" in request.GET,
        "map_container_id": request.GET.get("map_container_id", "carte"),
    }

    if latitude and longitude and not displayed_acteur.is_digital:
        context.update(
            itineraire_url=generate_google_maps_itineraire_url(
                latitude, longitude, displayed_acteur
            )
        )

    return render(request, "ui/pages/acteur.html", context)


def solution_admin(request, identifiant_unique):
    revision_acteur = RevisionActeur.objects.filter(
        identifiant_unique=identifiant_unique
    ).first()

    if revision_acteur:
        return redirect(revision_acteur.change_url)
    acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
    return redirect(acteur.change_url)
