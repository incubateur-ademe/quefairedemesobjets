import hashlib
import json
import logging
from typing import Any, TypedDict, override

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.db.models import Q
from django.forms import Form
from django.utils.functional import cached_property
from django.views.generic import DetailView

from core.constants import DEFAULT_MAP_CONTAINER_ID, MAP_CONTAINER_ID
from qfdmd.models import Produit
from qfdmo.forms import (
    ActionDirectionForm,
    AutoSubmitLegendeForm,
    FiltresForm,
    FiltresFormWithoutSynonyme,
    LegacySupportForm,
    LegendeForm,
    MapForm,
    ViewModeForm,
)
from qfdmo.models import CarteConfig
from qfdmo.models.action import Action
from qfdmo.views.adresses import SearchActeursView

logger = logging.getLogger(__name__)


class ViewModeFormEntry(TypedDict):
    form: type[ViewModeForm]
    prefix: str


class MapFormEntry(TypedDict):
    form: type[MapForm]
    prefix: str


class FiltresFormEntry(TypedDict):
    form: type[FiltresForm]
    prefix: str


class LegendeFormEntry(TypedDict):
    form: type[LegendeForm]
    prefix: str
    other_prefixes_to_check: list[str]


class AutoSubmitLegendeFormEntry(TypedDict):
    form: type[AutoSubmitLegendeForm]
    prefix: str
    other_prefixes_to_check: list[str]


class CarteForms(TypedDict):
    map: MapFormEntry
    view_mode: ViewModeFormEntry
    filtres: FiltresFormEntry
    legende: AutoSubmitLegendeFormEntry
    legende_filtres: LegendeFormEntry


class CarteFormsInstance(TypedDict):
    view_mode: None | ViewModeForm
    filtres: None | FiltresForm
    legende: None | AutoSubmitLegendeForm
    legende_filtres: None | LegendeForm


class CarteSearchActeursView(SearchActeursView):
    is_carte = True
    template_name = "ui/pages/carte.html"
    # TODO: voir si on peut mettre à None ici
    form_class = MapForm
    filtres_form_class = FiltresForm

    @override
    def _should_show_results(self):
        return True
        # self._get_ui_form("map").is_bound

    @property
    def forms(self) -> CarteForms:
        return {
            "map": {
                "form": MapForm,
                "prefix": "map",
            },
            "view_mode": {
                "form": ViewModeForm,
                "prefix": "view_mode",
            },
            "filtres": {
                "form": self.filtres_form_class,
                "prefix": "filtres",
            },
            "legende": {
                "form": AutoSubmitLegendeForm,
                "prefix": "legende",
                "other_prefixes_to_check": ["legende_filtres"],
            },
            "legende_filtres": {
                "form": LegendeForm,
                "prefix": "legende_filtres",
                "other_prefixes_to_check": ["legende"],
            },
        }

    def _generate_prefix(self, prefix: str) -> str:
        try:
            id = self.request.GET[MAP_CONTAINER_ID]
            return f"{id}_{prefix}"
        except (KeyError, AttributeError):
            return prefix

    # Legacy querystring support
    # ==========================
    def _initialize_legacy_form(self, data):
        """Initialize legacy support form from request data.

        Returns the form if it contains a valid querystring, None otherwise.
        """
        legacy_form = LegacySupportForm(data if data else None, request=self.request)
        return legacy_form if legacy_form["querystring"] else None

    def _get_legacy_form(self):
        """Cache and return the legacy form if it exists.

        This makes the legacy form accessible throughout the view hierarchy
        without re-initializing it multiple times.
        """
        if not hasattr(self, "_cached_legacy_form"):
            data = self.request.GET
            self._cached_legacy_form = self._initialize_legacy_form(data)
        return self._cached_legacy_form

    def _get_sous_categorie_ids_from_legacy_querystring(self) -> set[int]:
        """Extract sous_categorie IDs from legacy querystring if present.

        This method checks for the SOUS_CATEGORIE_QUERY_PARAM in the legacy
        querystring and returns a set of IDs. Returns empty set if no legacy
        querystring or no sous_categorie IDs found.

        Querystring parameters override carte_config.
        """
        legacy_form = self._get_legacy_form()
        if not legacy_form:
            return set()

        ids_from_request = legacy_form.decode_querystring().getlist("sc_id")

        if ids_from_request:
            return {int(id_) for id_ in ids_from_request if id_}

        return set()

    def _get_epci_codes(self) -> list[str]:
        legacy_form = self._get_legacy_form()
        if not legacy_form:
            return []
        return legacy_form.decode_querystring().getlist("epci_codes")

    # Forms and field utilities
    # =========================
    def _create_form_instance(self, form_class, data, prefix, legacy_form):
        return form_class(
            data,
            prefix=prefix,
            carte_config=self.carte_config,
            legacy_form=legacy_form,
        )

    def _get_bounded_form_with_fallback(self, form_config, data, legacy_form):
        primary_prefix = self._generate_prefix(form_config["prefix"])
        form = self._create_form_instance(
            form_config["form"], data, primary_prefix, legacy_form
        )
        if form.is_valid():
            return form

        for fallback_prefix in form_config.get("other_prefixes_to_check", []):
            generated_prefix = self._generate_prefix(fallback_prefix)
            fallback_form = self._create_form_instance(
                form_config["form"], data, generated_prefix, legacy_form
            )
            if fallback_form.is_valid():
                return fallback_form

        return form

    def _get_forms(self) -> CarteFormsInstance:
        data = self.request.GET
        legacy_form = self._get_legacy_form()

        form_instances: CarteFormsInstance = {}
        if legacy_form:
            form_instances["legacy"] = legacy_form

        for key, form_config in self.forms.items():
            form_instances[key] = self._get_bounded_form_with_fallback(
                form_config, data, legacy_form
            )

        return form_instances

    def _get_ui_form(self, form_name) -> Form | None:
        try:
            return self.ui_forms[form_name]
        except KeyError:
            return None

    def _get_field_value_for(self, form_name: str, field_name: str) -> Any:
        try:
            return self._get_ui_form(form_name)[field_name].value()
        except (AttributeError, KeyError):
            return None

    # Form field accessors
    # ====================
    def _get_direction(self):
        action_direction_form = ActionDirectionForm(self.request.GET)
        return action_direction_form["direction"].value()

    def _get_ess(self):
        return self._check_if_label_qualite_is_set("ess")

    def _get_legacy_label_reparacteur(self):
        legacy_form = self._get_legacy_form()
        if not legacy_form:
            return False

        # TODO : handle initial values
        return legacy_form.decode_querystring().get("label_reparacteur")

    def _get_label_reparacteur(self):
        return self._check_if_label_qualite_is_set("reparacteur")

    def _get_bonus(self):
        return self._get_field_value_for("filtres", "bonus")

    def _get_pas_exclusivite_reparation(self) -> bool:
        return self._get_field_value_for("filtres", "pas_exclusivite_reparation")

    def _check_if_label_qualite_is_set(self, label):
        try:
            return label in self._get_field_value_for("filtres", "label_qualite")
        except (TypeError, KeyError):
            return False

    def _get_map_container_id(self):
        if self.carte_config:
            return self.carte_config.slug
        return DEFAULT_MAP_CONTAINER_ID

    def _get_bounding_box(self) -> str | None:
        """Get bounding_box from the bounded map form.

        Override parent to use the bounded map form when available,
        falling back to parent behavior if form is not available or invalid.
        """
        return self._get_field_value_for("map", "bounding_box")

    def _get_epci_codes(self):
        # TODO: récupérer PR epci
        pass

    def _get_latitude(self):
        return self._get_field_value_for("map", "latitude")

    def _get_longitude(self):
        return self._get_field_value_for("map", "longitude")

    def _get_carte_config(self):
        return None

    @cached_property
    def carte_config(self) -> CarteConfig | None:
        return self._get_carte_config()

    def _get_max_displayed_acteurs(self):
        if self.carte_config and self.carte_config.nombre_d_acteurs_affiches:
            return self.carte_config.nombre_d_acteurs_affiches
        if self.request.GET.get("limit", "").isnumeric():
            return int(self.request.GET.get("limit"))
        return settings.CARTE_MAX_SOLUTION_DISPLAYED

    def _get_cache_key_for_acteurs(self):
        """Generate a cache key based on query parameters, excluding view mode.

        This allows caching the acteurs queryset when users switch between
        carte and liste modes without hitting the database again.
        """
        # Get all query parameters except view mode
        params_dict = self.request.GET.copy()

        # Remove parameters that don't affect the acteurs queryset
        params_to_exclude = [
            # View mode parameters
            f"{self._generate_prefix('view_mode')}-view",
            "view_mode-view",
            # Pagination
            "page",
            # UI state parameters that don't affect query results
            "carte",
            "querystring",
        ]

        for param in params_to_exclude:
            params_dict.pop(param, None)

        # Sort parameters for consistent cache keys
        sorted_params = sorted(params_dict.items())
        params_string = json.dumps(sorted_params, sort_keys=True)

        # Create a hash of the parameters
        params_hash = hashlib.md5(params_string.encode()).hexdigest()

        return f"acteurs_queryset:{params_hash}"

    def _build_acteurs_queryset_from_location(self, acteurs, **kwargs):
        """Override parent to reorder by distance after limiting.

        In carte mode, after limiting the queryset to max_displayed_acteurs,
        we reorder by distance from the center point to ensure the closest
        acteurs are shown first on the map.

        Also implements caching: when users switch between carte and liste modes,
        the acteurs list is cached for 60 seconds to avoid hitting the database again.
        """
        # Try to get cached acteurs if available
        cache_key = self._get_cache_key_for_acteurs()
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            # Return cached bbox and acteurs
            return cached_result

        bbox, acteurs = super()._build_acteurs_queryset_from_location(acteurs, **kwargs)

        # In mode liste, we want to sort by distance but do not annotate before
        # filtering and limiting so that we do not annotate the whole database.
        # Instead, we annotate here after the queryset has been limited.
        location = getattr(self, "location", None)
        if not getattr(acteurs, "_has_distance_field", False) and location:
            location_data = json.loads(location)
            reference_point = Point(
                location_data["longitude"], location_data["latitude"], srid=4326
            )
            # Convert to list and sort in Python since queryset is already sliced
            acteurs_list = list(acteurs)
            for acteur in acteurs_list:
                acteur.distance = acteur.location.distance(reference_point)
            acteurs = sorted(acteurs_list, key=lambda a: a.distance)
        elif getattr(acteurs, "_has_distance_field", False):
            # Only reorder via SQL if queryset hasn't been sliced yet
            try:
                acteurs = acteurs.order_by("distance")
            except TypeError:
                # Queryset was already sliced, convert to list and sort
                acteurs = sorted(list(acteurs), key=lambda a: a.distance)

        # Cache the result for 60 seconds
        result = (bbox, acteurs)
        cache.set(cache_key, result, 60)

        return bbox, acteurs

    def get_context_data(self, **kwargs):
        self.ui_forms = self._get_forms()
        self.paginate = (
            self.ui_forms["view_mode"]["view"].value()
            == ViewModeForm.ViewModeSegmentedControlChoices.LISTE
        )
        # QuerySet is built in SearchActeursView.get_context_data method,
        # it needs to be kept after the forms are initialised above.
        context = super().get_context_data(**kwargs)

        # TODO address_ok in result.html use this epci_codes from context
        # when address_ok will be remove from template and the condition will be
        # initialized from view, this context assignation will be removed
        context["epci_codes"] = []
        if epci_codes := self._get_epci_codes():
            context["epci_codes"] = epci_codes

        carte_config = self._get_carte_config()
        icon_lookup = self._build_icon_lookup(carte_config) if carte_config else {}

        context.update(
            forms=self.ui_forms,
            map_container_id=self._get_map_container_id(),
            mode_liste=self.paginate,
            carte_config=carte_config,
            selected_action_codes=self._get_action_codes(),
            icon_lookup=icon_lookup,
        )

        return context

    def _build_icon_lookup(self, carte_config):
        """Build a lookup dictionary for icon configurations.

        This precomputes the icon URLs for all action/acteur_type combinations
        to avoid N+1 queries in the template tag.

        Only includes icons for groupe_actions that are currently selected by the user.

        Returns a dict with keys like: ('action_code', 'acteur_type_code') -> icon_url
        and also: ('action_code', None) -> icon_url for configs without acteur_type
        """
        if not carte_config:
            return {}

        icon_lookup = {}

        # Get the selected groupe_action IDs to filter configs
        selected_groupe_action_ids = set(
            int(id)
            for id in self._get_ui_form("legende")["groupe_action"].value() or []
        )

        if not selected_groupe_action_ids:
            return {}

        # Prefetch all groupe_action_configs with their relations
        configs = carte_config.groupe_action_configs.select_related(
            "groupe_action", "acteur_type"
        ).prefetch_related("groupe_action__actions")

        for config in configs:
            if not config.icon:
                continue

            # Only include icons for selected groupe_actions
            if (
                config.groupe_action
                and config.groupe_action.id not in selected_groupe_action_ids
            ):
                continue

            # Get action codes for this groupe_action
            if config.groupe_action:
                # Work with prefetched data to avoid N+1 queries
                action_codes = [
                    action.code for action in config.groupe_action.actions.all()
                ]
            else:
                # Config applies to all actions
                action_codes = [None]

            acteur_type_code = config.acteur_type.code if config.acteur_type else None

            # Store the icon URL for each action/acteur_type combination
            for action_code in action_codes:
                key = (action_code, acteur_type_code)
                # Only store if not already set (first match wins)
                if key not in icon_lookup:
                    icon_lookup[key] = config.icon.url

        return icon_lookup

    def _get_action_ids(self) -> list[str]:
        groupe_action_ids = self._get_ui_form("legende")["groupe_action"].value()

        # TODO: check if useful as these two forms are now synced
        for form in [
            self._get_ui_form("legende"),
            self._get_ui_form("legende_filtres"),
        ]:
            if form and form.is_valid():
                groupe_action_ids = form["groupe_action"].value()

        # Convert to list to avoid generating a subquery in the final SQL
        # This optimizes the query by using a direct IN clause instead of a subquery

        return list(
            Action.objects.filter(groupe_action__id__in=groupe_action_ids)
            .only("id")
            .values_list("id", flat=True)
        )

    def _get_action_codes(self) -> str:
        """Get selected action codes as a pipe-separated string for use in templates.

        This converts the selected groupe_action IDs to action codes that can be
        passed to acteur_pinpoint_tag.
        """
        groupe_action_ids = self._get_ui_form("legende")["groupe_action"].value()

        # TODO: check if useful as these two forms are now synced
        for form in [
            self._get_ui_form("legende"),
            self._get_ui_form("legende_filtres"),
        ]:
            if form and form.is_valid():
                groupe_action_ids = form["groupe_action"].value()

        # Get action codes for the selected groupe_actions
        action_codes = list(
            Action.objects.filter(groupe_action__id__in=groupe_action_ids)
            .only("code")
            .values_list("code", flat=True)
        )

        return "|".join(action_codes)

    def _get_sous_categorie_ids(self) -> list[int]:
        """Get sous_categorie IDs from synonyme field and legacy querystring.

        Legacy querystring parameters override other sources if present.
        """
        # Check for legacy querystring first (it overrides everything)
        legacy_ids = self._get_sous_categorie_ids_from_legacy_querystring()
        if legacy_ids:
            return list(legacy_ids)

        # Fall back to synonyme field
        synonyme_id = self._get_field_value_for("filtres", "synonyme")
        if not synonyme_id:
            return []

        return list(
            Produit.objects.filter(synonymes__id__in=[synonyme_id]).values_list(
                "sous_categories__id", flat=True
            )
        )


class CarteConfigView(DetailView, CarteSearchActeursView):
    model = CarteConfig
    context_object_name = "carte_config"
    filtres_form_class = FiltresFormWithoutSynonyme

    def get_queryset(self):
        """Optimize queries by prefetching all ManyToMany relations"""
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "source",
                "label_qualite",
                "acteur_type",
                "sous_categorie_objet",
                "groupe_action",
                "groupe_action__actions",
                "action",
                "direction",
                "direction__actions",
                "epci",
            )
        )

    def _get_max_displayed_acteurs(self):
        # Hardcoded value taken from dict previously used
        return 25

    @override
    def _get_carte_config(self):
        """Cache the object to avoid repeated queries"""
        return self.get_object()

    @override
    def _compile_acteurs_queryset(self, *args, **kwargs):
        filters, excludes = super()._compile_acteurs_queryset(*args, **kwargs)

        # TODO: remove this
        if source_filter := self.carte_config.source.all():
            filters &= Q(source__in=source_filter)

        # TODO: remove this
        if label_filter := self.carte_config.label_qualite.all():
            filters &= Q(labels__in=label_filter)

        # TODO: remove this
        if acteur_type_filter := self.carte_config.acteur_type.all():
            filters &= Q(acteur_type__in=acteur_type_filter)

        return filters, excludes

    def _get_sous_categorie_ids(self) -> list[int]:
        """Get sous_categorie IDs with the following priority:
        1. Legacy querystring (overrides everything) - handled in parent
        2. Parent implementation (synonyme field + legacy querystring)
        3. CarteConfig sous_categorie_objet filter

        Results are intersected when multiple sources provide IDs.
        """
        result_ids = set(super()._get_sous_categorie_ids())

        # Apply carte_config filter if present
        if sous_categorie_filter := self.carte_config.sous_categorie_objet.values_list(
            "id", flat=True
        ):
            filter_ids = set(sous_categorie_filter)
            result_ids = result_ids & filter_ids if result_ids else filter_ids

        return list(result_ids)

    def _get_epci_codes(self) -> list[str]:
        epci_codes = super()._get_epci_codes()
        if not epci_codes:
            epci_codes = self.carte_config.epci.all().values_list("code", flat=True)

        return epci_codes

    def _get_action_ids(self) -> list[str]:
        action_ids = super()._get_action_ids()

        if groupe_action_filter := self.carte_config.groupe_action.all():
            action_ids = list(
                set(groupe_action_filter.values_list("actions__id", flat=True))
                & set(action_ids)
            )

        if action_filter := self.carte_config.action.all():
            action_ids = list(
                set(action_filter.values_list("id", flat=True)) & set(action_ids)
            )

        if direction_filter := self.carte_config.direction.all():
            action_ids = list(
                set(direction_filter.values_list("actions__id", flat=True))
                & set(action_ids)
            )

        return action_ids
