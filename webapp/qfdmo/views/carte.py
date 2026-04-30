import hashlib
import json
import logging
from typing import Any, NotRequired, TypedDict, override

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.cache import cache
from django.db import connection
from django.db.models import Exists, OuterRef, Q
from django.forms import Form
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.functional import cached_property
from django.views.generic import DetailView

from core.constants import DEFAULT_MAP_CONTAINER_ID, MAP_CONTAINER_ID
from qfdmd.models import Produit
from qfdmo.constants import MAP_FORM_PREFIX
from qfdmo.forms import (
    ActionDirectionForm,
    AutoSubmitLegendeForm,
    FiltresForm,
    FiltresFormWithoutSynonyme,
    LegacySupportForm,
    LegendeForm,
    MapForm,
    ViewModeForm,
    generate_form_prefix,
)
from qfdmo.models import (
    ActeurStatus,
    CarteConfig,
    DisplayedActeur,
    DisplayedPropositionService,
    LabelQualite,
)
from qfdmo.models.action import Action
from qfdmo.views.adresses import AbstractSearchActeursView, MapPrefixMixin

logger = logging.getLogger(__name__)

# Cap for /carte/acteurs.geojson responses. Higher than the legacy
# CARTE_MAX_SOLUTION_DISPLAYED (which gates the list view) because spatial
# thinning prevents the marker density from getting overwhelming on the map.
CARTE_GEOJSON_MAX_FEATURES = 200

# Default spatial thinning grid step in degrees, used as a floor when the
# frontend doesn't send a zoom level. Real grid is computed per-request from
# the bbox-center latitude and the user's zoom (see _grid_step_for_zoom).
CARTE_GEOJSON_GRID_DEG = 0.005

# Target on-screen cell size in pixels. We size the thinning grid so each
# cell maps to roughly this many CSS pixels at the user's current zoom — a
# trade-off between marker density (smaller = more markers) and visual
# clutter (smaller = icons overlap). 20 px at the marker icon's ~50 px width
# allows ~2.5 markers per icon-width before overlap, which reads as "evenly
# spread" on the user's screen.
CARTE_GEOJSON_TARGET_CELL_PX = 20


class ViewModeFormEntry(TypedDict):
    form: type[ViewModeForm]
    prefix: str
    other_prefixes_to_check: NotRequired[list[str]]


class MapFormEntry(TypedDict):
    form: type[MapForm]
    prefix: str
    other_prefixes_to_check: NotRequired[list[str]]


class FiltresFormEntry(TypedDict):
    form: type[FiltresForm]
    prefix: str
    other_prefixes_to_check: NotRequired[list[str]]


class LegendeFormEntry(TypedDict):
    form: type[LegendeForm]
    prefix: str
    other_prefixes_to_check: NotRequired[list[str]]


class AutoSubmitLegendeFormEntry(TypedDict):
    form: type[AutoSubmitLegendeForm]
    prefix: str
    other_prefixes_to_check: NotRequired[list[str]]


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
    map: None | MapForm


class CarteSearchActeursView(MapPrefixMixin, AbstractSearchActeursView):
    is_carte = True
    template_name = "ui/pages/carte.html"
    # TODO: voir si on peut mettre à None ici
    form_class = MapForm
    filtres_form_class = FiltresForm

    @override
    def _should_show_results(self):
        return (
            self._get_field_value_for("map", "adresse")
            or self._get_bounding_box()
            or self._get_latitude()
            or self._get_epci_codes()
        )

    @property
    def forms(self) -> CarteForms:
        return {
            "map": {
                "form": MapForm,
                "prefix": MAP_FORM_PREFIX,
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

    def _generate_prefix(self, prefix: str = MAP_FORM_PREFIX) -> str:
        return generate_form_prefix(id=self._get_map_container_id(), prefix=prefix)

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
        base_prefix = form_config["prefix"]

        form = self._create_form_instance(
            form_config["form"], data, primary_prefix, legacy_form
        )
        if form.is_valid():
            return form

        # If the primary prefix includes map_container_id and the form is invalid,
        # try the base prefix without map_container_id as a fallback
        # TODO: understand why this is necessary.
        if primary_prefix != base_prefix:
            base_form = self._create_form_instance(
                form_config["form"], data, base_prefix, legacy_form
            )
            if base_form.is_valid():
                return base_form

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

        if MAP_CONTAINER_ID in self.request.GET:
            return self.request.GET[MAP_CONTAINER_ID]

        return DEFAULT_MAP_CONTAINER_ID

    def _get_bounding_box(self) -> str | None:
        """Get bounding_box from the bounded map form.

        Override parent to use the bounded map form when available,
        falling back to parent behavior if form is not available or invalid.
        """
        return self._get_field_value_for("map", "bounding_box")

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
            # Sort by distance in Python (queryset already sliced, can't use SQL)
            try:
                location_data = json.loads(location)
                longitude = float(location_data.get("longitude"))
                latitude = float(location_data.get("latitude"))

                reference_point = Point(longitude, latitude, srid=4326)
                acteurs_list = list(acteurs)
                for acteur in acteurs_list:
                    acteur.distance = acteur.location.distance(reference_point)
                acteurs = sorted(acteurs_list, key=lambda a: a.distance)
            except (ValueError, TypeError, KeyError) as e:
                # Invalid/missing coordinates, skip distance sorting
                logger.warning(
                    "Invalid coordinates for distance calculation: error=%s",
                    type(e).__name__,
                )
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
        view_mode = self._get_field_value_for("view_mode", "view")
        self.paginate = view_mode == ViewModeForm.ViewModeSegmentedControlChoices.LISTE
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

        search_area_citycode = (
            self._get_field_value_for("map", "search_area_citycode") or ""
        )
        # Pre-resolve the polygon bbox at render time so the map controller
        # can fit the camera synchronously on connect (no jolt when the
        # polygon fetch lands later).
        search_area_bbox = self._build_search_area_bbox(search_area_citycode)

        context.update(
            forms=self.ui_forms,
            map_container_id=self._get_map_container_id(),
            mode_liste=self.paginate,
            carte_config=carte_config,
            selected_action_codes=self._get_action_codes(),
            icon_lookup=icon_lookup,
            geojson_filter_params=self._build_geojson_filter_params(),
            search_area_citycode=search_area_citycode,
            search_area_bbox=search_area_bbox,
        )

        return context

    def _build_search_area_bbox(self, citycode: str) -> str:
        """Return the polygon bbox as a JSON string in the frontend's standard
        shape ({southWest, northEast}), pulled from the same Django cache the
        commune-geojson proxy uses. Empty string when not available.
        """
        if not citycode:
            return ""
        from qfdmo.geo_api import retrieve_commune_geojson_from_api_or_cache

        feature = retrieve_commune_geojson_from_api_or_cache(citycode)
        if not feature or "geometry" not in feature:
            return ""
        try:
            geometry = GEOSGeometry(json.dumps(feature["geometry"]))
            xmin, ymin, xmax, ymax = geometry.extent
        except Exception:
            return ""
        return json.dumps(
            {
                "southWest": {"lng": xmin, "lat": ymin},
                "northEast": {"lng": xmax, "lat": ymax},
            }
        )

    def _build_geojson_filter_params(self) -> str:
        """Build the query-string fragment the frontend sends to
        carte/acteurs.geojson on each pan, so the auto-fetch honours the
        currently-applied filters (groupe_actions, bonus, ess, sous_categories).
        Returned as a `&`-joined string ready to append to the request URL.
        """
        from urllib.parse import urlencode

        params: list[tuple[str, str]] = []

        groupe_action_ids = self._get_ui_form("legende")["groupe_action"].value() or []
        if groupe_action_ids:
            params.append(("groupe_actions", ",".join(str(g) for g in groupe_action_ids)))

        if self._get_bonus():
            params.append(("bonus", "1"))
        if self._get_ess():
            params.append(("ess", "1"))

        sous_categorie_ids = self._get_sous_categorie_ids()
        if sous_categorie_ids:
            params.append(
                ("sous_categories", ",".join(str(s) for s in sous_categorie_ids))
            )

        return urlencode(params)

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

    @property
    def filtres_form_class(self):
        if self.object.cacher_filtre_objet:
            return FiltresFormWithoutSynonyme
        else:
            return super().filtres_form_class

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

    @override
    def _get_carte_config(self):
        """Cache the object to avoid repeated queries"""
        return self.get_object()

    @override
    def _compile_acteurs_queryset(self, *args, **kwargs):
        filters, excludes = super()._compile_acteurs_queryset(*args, **kwargs)

        # TODO: remove this
        if source_filter := self.carte_config.source.all():
            filters &= Q(sources__in=source_filter)

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


# Frontend icon names mirror static/to_compile/js/acteur_icons.ts:iconNameFor.
def _icon_name_for(groupe_action_code: str, bonus: bool) -> str:
    return f"acteur:{groupe_action_code}:bonus" if bonus else f"acteur:{groupe_action_code}"


def _resolve_icon(
    acteur, action_codes: str | None, sous_categorie_id: int | None
) -> tuple[str, bool]:
    """Pick the icon name + bonus flag for a single acteur, mirroring
    acteur_pinpoint_tag's logic for the carte path.
    """
    chosen = acteur.action_to_display(
        action_list=action_codes,
        sous_categorie_id=sous_categorie_id,
        carte=True,
    )
    if chosen is None:
        return ("", False)
    groupe_action = chosen.groupe_action or chosen
    code = getattr(groupe_action, "code", "") or ""
    bonus = code == "reparer" and getattr(acteur, "is_bonus_reparation", False)
    return (_icon_name_for(code, bonus), bonus)


def commune_geojson(request, citycode: str):
    """Proxy + cache the commune polygon from geo.api.gouv.fr.

    Frontend hits this same-origin endpoint instead of geo.api.gouv.fr
    directly: avoids CORS, multiplexes with the rest of the page over HTTP/2,
    and lets us cache the polygon server-side (~10 ms reads after first hit).
    """
    if not citycode.isdigit() or not (4 <= len(citycode) <= 5):
        return HttpResponseBadRequest("invalid citycode")

    from qfdmo.geo_api import retrieve_commune_geojson_from_api_or_cache

    feature = retrieve_commune_geojson_from_api_or_cache(citycode)
    if feature is None:
        return JsonResponse({"error": "not found"}, status=404)

    response = JsonResponse(feature)
    # Browsers can cache the polygon for the session; the upstream rarely
    # changes commune outlines.
    response["Cache-Control"] = "public, max-age=86400"
    return response


def _grid_step_for_zoom(zoom: float, center_lat: float) -> float:
    """Compute the spatial-thinning grid step in degrees so each cell occupies
    ~CARTE_GEOJSON_TARGET_CELL_PX on screen at the given zoom.

    Web-mercator meters-per-pixel: 156543.03 * cos(lat) / 2**zoom.
    Convert target_meters → degrees of longitude at this latitude:
        deg_lng = meters / (111320 * cos(lat))
    Combining: deg_lng = TARGET_PX * 156543 * cos(lat) / 2**zoom / (111320 * cos(lat))
                       = TARGET_PX * 1.406 / 2**zoom
    The cos(lat) cancels because mercator's m/px and lng-deg/m both scale by
    cos(lat). Latitude degrees stay constant (1° lat ≈ 111 km everywhere) so
    we use the same step for both axes — visually square at the bbox center.
    """
    if zoom <= 0:
        return CARTE_GEOJSON_GRID_DEG
    return max(
        0.0001,  # floor: never tighter than ~10 m
        CARTE_GEOJSON_TARGET_CELL_PX * 1.406 / (2**zoom),
    )


def _apply_acteurs_filters(pk_qs, request):
    """Apply the optional filter query params (sous_categories, groupe_actions,
    bonus, ess, exclude_uuids) to a DisplayedActeur PK queryset and return:
        (filtered_qs, sc_ids, selected_action_ids).

    Shared between the bbox and KNN endpoints so the filter contract stays
    consistent across both shapes.
    """
    if exclude_raw := request.GET.get("exclude_uuids", "").strip():
        exclude_uuids = [u for u in exclude_raw.split(",") if u]
        if exclude_uuids:
            pk_qs = pk_qs.exclude(uuid__in=exclude_uuids)

    sc_ids: list[int] = []
    if sc_raw := request.GET.get("sous_categories", "").strip():
        sc_ids = [int(s) for s in sc_raw.split(",") if s.isdigit()]
        if sc_ids:
            pk_qs = pk_qs.filter(
                Exists(
                    DisplayedPropositionService.objects.filter(
                        acteur_id=OuterRef("pk"),
                        sous_categories__id__in=sc_ids,
                    )
                )
            )

    selected_action_ids: list[int] = []
    if ga_raw := request.GET.get("groupe_actions", "").strip():
        ga_ids = [int(g) for g in ga_raw.split(",") if g.isdigit()]
        if ga_ids:
            selected_action_ids = list(
                Action.objects.filter(groupe_action_id__in=ga_ids).values_list(
                    "id", flat=True
                )
            )
            pk_qs = pk_qs.filter(
                Exists(
                    DisplayedPropositionService.objects.filter(
                        acteur_id=OuterRef("pk"),
                        action_id__in=selected_action_ids,
                    )
                )
            )

    if request.GET.get("bonus") == "1":
        pk_qs = pk_qs.filter(
            Exists(
                LabelQualite.objects.filter(
                    displayedacteur=OuterRef("pk"), bonus=True
                )
            )
        )
    if request.GET.get("ess") == "1":
        pk_qs = pk_qs.filter(
            Exists(
                LabelQualite.objects.filter(
                    displayedacteur=OuterRef("pk"), code="ess"
                )
            )
        )

    return pk_qs, sc_ids, selected_action_ids


def _serialize_acteurs(
    pks_in_order: list,
    sc_ids: list[int],
    selected_action_ids: list[int],
) -> list[dict]:
    """Hydrate the ordered PK list into prefetched acteur instances and emit
    GeoJSON features. Preserves the input order (required for KNN's nearest-
    first ordering).
    """
    if not pks_in_order:
        return []

    instances = {
        a.pk: a
        for a in DisplayedActeur.objects.filter(pk__in=pks_in_order).prefetch_related(
            "proposition_services__action__groupe_action",
            "proposition_services__sous_categories",
            "action_principale",
            "labels",
        )
    }

    sc_id_for_action = sc_ids[0] if sc_ids else None
    action_codes = (
        "|".join(
            Action.objects.filter(id__in=selected_action_ids).values_list(
                "code", flat=True
            )
        )
        if selected_action_ids
        else None
    )

    features = []
    for pk in pks_in_order:
        acteur = instances.get(pk)
        if acteur is None or acteur.location is None:
            continue
        icon, bonus = _resolve_icon(
            acteur, action_codes=action_codes, sous_categorie_id=sc_id_for_action
        )
        if not icon:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [acteur.location.x, acteur.location.y],
                },
                "properties": {
                    "uuid": str(acteur.uuid),
                    "icon": icon,
                    "bonus": bonus,
                    "detail_url": acteur.get_absolute_url(),
                },
            }
        )
    return features


def carte_acteurs_near_geojson(request):
    """K-nearest-neighbor endpoint for "show me the N closest acteurs to this
    point" — used when the user picks a non-municipality address (street /
    housenumber / locality) from the autocomplete. Postgres walks the GiST
    index in distance order via the `<->` operator; single query, no radius
    iteration.

    Query params:
        lat, lng: required, the search center.
        count: target number of features, default 30, capped at
            settings.CARTE_MAX_SOLUTION_DISPLAYED.
        sous_categories, groupe_actions, bonus, ess, exclude_uuids: same
            filter contract as carte_acteurs_geojson.
    """
    try:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])
    except (KeyError, ValueError):
        return HttpResponseBadRequest("missing or invalid lat/lng")

    count = 30
    if (raw := request.GET.get("count", "")) and raw.isdigit():
        count = min(int(raw), settings.CARTE_MAX_SOLUTION_DISPLAYED)

    pk_qs = DisplayedActeur.objects.filter(
        statut=ActeurStatus.ACTIF,
    ).exclude(location__isnull=True)

    pk_qs, sc_ids, selected_action_ids = _apply_acteurs_filters(pk_qs, request)

    # `<->` is the GiST-indexed distance operator. Postgres walks the spatial
    # index in nearest-first order, so this returns the K closest acteurs in
    # one indexed pass — no full-scan, no random sort, no iteration.
    #
    # Django's `Distance()` function expands to `ST_Distance(...)`, which is
    # NOT eligible for the GiST index — Postgres falls back to a parallel
    # seq scan computing precise geography distances for every row. The
    # `<->` operator IS GiST-indexed for geography columns, so we drop into
    # raw SQL for the order-by.
    pks_in_order = list(
        pk_qs.values_list("pk", flat=True)
        .extra(  # noqa: SLF001
            select={"_knn_dist": "location <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography"},
            select_params=[lng, lat],
            order_by=["_knn_dist"],
        )[:count]
    )

    features = _serialize_acteurs(pks_in_order, sc_ids, selected_action_ids)

    return JsonResponse(
        {
            "type": "FeatureCollection",
            "features": features,
            # KNN never truncates: it returns up to `count`, all that exist
            # if the dataset has fewer.
            "truncated": False,
        },
        json_dumps_params={"separators": (",", ":")},
    )


def carte_acteurs_geojson(request):
    """GeoJSON endpoint feeding the carte's MapLibre symbol layer.

    Returns a FeatureCollection of acteur Points filtered by bbox and any
    optional filters. Used to incrementally append acteurs as the user pans
    the map without re-rendering the whole results frame.

    Query params:
        bbox: "<sw_lng>,<sw_lat>,<ne_lng>,<ne_lat>"
        exclude_uuids: comma-separated list of UUIDs already on screen
        sous_categories: comma-separated list of ids
        groupe_actions: comma-separated list of group_action ids
        bonus: "1" to keep only acteurs with the bonus label
        ess: "1" to keep only ESS-labelled acteurs
        limit: optional, capped at settings.CARTE_MAX_SOLUTION_DISPLAYED
    """
    bbox_raw = request.GET.get("bbox", "").strip()
    if not bbox_raw:
        return HttpResponseBadRequest("missing bbox")
    try:
        sw_lng, sw_lat, ne_lng, ne_lat = (float(x) for x in bbox_raw.split(","))
    except ValueError:
        return HttpResponseBadRequest("invalid bbox")

    # Zoom-aware spatial thinning: cell size scales with the user's zoom so
    # markers stay visually distributed at every zoom level (a fixed 500 m
    # cell looks fine at city zoom but stacks all features into one pixel
    # when looking at the whole country).
    try:
        zoom = float(request.GET.get("zoom", ""))
    except ValueError:
        zoom = 0.0
    center_lat = (sw_lat + ne_lat) / 2.0
    grid_step = _grid_step_for_zoom(zoom, center_lat)

    # Step 1: build the *filter* queryset over PKs only. No DISTINCT, no
    # ORDER BY, no prefetches — the goal is keep the planner's job small and
    # let JOIN-producing filters (labels__*, proposition_services__*) live
    # as Exists() subqueries that don't duplicate rows.
    #
    # Spatial predicate: raw geography `&&` (bbox-overlap operator) against
    # an envelope cast to geography. This is what the existing
    # `exposure_carte_acteur_location_idx` GiST index actually supports —
    # the ORM's `location__coveredby` expands to ST_CoveredBy, which forces
    # a parallel seq scan recomputing precise geography distances per row
    # (~580 ms × 2 workers + 2 s of JIT compilation on a France-wide bbox).
    # `&&` is bbox-only and lets Postgres choose between an index scan
    # (small bbox) and a cheap parallel seq scan (wide bbox). Cuts the
    # France-wide query from ~3 s to ~300 ms.
    pk_qs = DisplayedActeur.objects.filter(
        statut=ActeurStatus.ACTIF,
    ).exclude(location__isnull=True).extra(  # noqa: SLF001
        where=[
            "location && ST_MakeEnvelope(%s, %s, %s, %s, 4326)::geography",
        ],
        params=[sw_lng, sw_lat, ne_lng, ne_lat],
    )

    pk_qs, sc_ids, selected_action_ids = _apply_acteurs_filters(pk_qs, request)

    # Cap separate from CARTE_MAX_SOLUTION_DISPLAYED (which still gates the
    # legacy list view). The JSON endpoint can return more because spatial
    # thinning prevents the marker density from getting overwhelming.
    limit = CARTE_GEOJSON_MAX_FEATURES
    if (raw := request.GET.get("limit", "")) and raw.isdigit():
        limit = min(int(raw), CARTE_GEOJSON_MAX_FEATURES)

    # Step 2: spatially thin the bbox down to one acteur per grid cell, then
    # cap. ST_SnapToGrid buckets every acteur into a lat/lng cell sized so
    # it maps to ~CARTE_GEOJSON_TARGET_CELL_PX on screen at the user's
    # current zoom; GROUP BY collapses each bucket; array_agg(... ORDER BY
    # random())[1] picks one acteur per cell uniformly so dense areas like
    # central Paris show a representative sample instead of whatever
    # Postgres has at the head of physical storage. Visually evenly
    # distributed at every zoom; avoids icon-on-icon clutter.
    #
    # We wrap the ORM-built filter queryset (with Exists() filters already
    # applied, selecting both identifiant_unique and location) as the FROM
    # clause. Postgres flattens the subquery and runs the entire pipeline
    # in a single pass — geometry `&&` index lookup at high zoom, parallel
    # seq scan at low zoom — avoiding the row-by-row PK lookup that an
    # explicit JOIN would force on a wide bbox.
    inner_sql, inner_params = pk_qs.values_list(
        "identifiant_unique", "location"
    ).query.sql_with_params()
    raw_sql = f"""
        SELECT (array_agg(filtered.identifiant_unique ORDER BY random()))[1]
        FROM ({inner_sql}) AS filtered
        GROUP BY ST_SnapToGrid(filtered.location::geometry, %s)
        LIMIT %s
    """
    raw_params = [*inner_params, grid_step, limit + 1]
    with connection.cursor() as cur:
        cur.execute(raw_sql, raw_params)
        sampled_pks = [row[0] for row in cur.fetchall()]
    truncated = len(sampled_pks) > limit
    sampled_pks = sampled_pks[:limit]

    features = _serialize_acteurs(sampled_pks, sc_ids, selected_action_ids)

    return JsonResponse(
        {
            "type": "FeatureCollection",
            "features": features,
            # Top-level flag, not strictly part of GeoJSON: signals to the
            # frontend that more acteurs exist in this bbox than we returned,
            # so a "zoom in to see more" pill should be shown.
            "truncated": truncated,
        },
        json_dumps_params={"separators": (",", ":")},
    )
