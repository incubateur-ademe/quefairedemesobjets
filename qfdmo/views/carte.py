import logging
from typing import Any, TypedDict, override

from django.conf import settings
from django.db.models import Q
from django.forms import Form
from django.utils.functional import cached_property
from django.views.generic import DetailView

from core.constants import MAP_CONTAINER_ID
from qfdmd.models import Produit
from qfdmo.forms import (
    ActionDirectionForm,
    AutoSubmitLegendeForm,
    CarteForm,
    FiltresForm,
    FiltresFormWithoutSynonyme,
    LegacySupportForm,
    LegendeForm,
    ViewModeForm,
)
from qfdmo.models import CarteConfig
from qfdmo.models.action import Action
from qfdmo.views.adresses import SearchActeursView

logger = logging.getLogger(__name__)


class ViewModeFormEntry(TypedDict):
    form: type[ViewModeForm]
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
    form_class = CarteForm
    filtres_form_class = FiltresForm

    @property
    def forms(self) -> CarteForms:
        return {
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

        ids_from_request = legacy_form.decode_querystring().getlist(
            CarteConfig.SOUS_CATEGORIE_QUERY_PARAM
        )

        if ids_from_request:
            return {int(id_) for id_ in ids_from_request if id_}

        return set()

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

    def _get_form(self, form_name) -> Form | None:
        try:
            return self._get_forms()[form_name]
        except KeyError:
            return None

    def _get_field_value_for(self, form_name: str, field_name: str) -> Any:
        try:
            return self._get_form(form_name)[field_name].value()
        except (AttributeError, KeyError):
            return None

    def _get_direction(self):
        action_direction_form = ActionDirectionForm(self.request.GET)
        return action_direction_form["direction"].value()

    def _get_ess(self):
        return self._check_if_label_qualite_is_set("ess")

    def _get_label_reparacteur(self):
        return self._check_if_label_qualite_is_set("reparacteur")

    def _get_bonus(self):
        return self._check_if_label_qualite_is_set("bonusrepar")

    def _check_if_label_qualite_is_set(self, label):
        try:
            return label in self._get_form("filtres")["label_qualite"].value()
        except (TypeError, KeyError):
            return False

    def _get_map_container_id(self):
        if self.carte_config:
            return self.carte_config.slug
        return "carte"

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

    def get_context_data(self, **kwargs):
        forms = self._get_forms()
        self.paginate = (
            forms["view_mode"]["view"].value()
            == ViewModeForm.ViewModeSegmentedControlChoices.LISTE
        )
        context = super().get_context_data(**kwargs)

        context.update(
            is_carte=True,
            forms=forms,
            map_container_id=self._get_map_container_id(),
            mode_liste=self.paginate,
            carte_config=self._get_carte_config(),
        )

        return context

    def _get_action_ids(self) -> list[str]:
        groupe_action_ids = self._get_form("legende")["groupe_action"].value()

        # TODO: check if useful as these two forms are now synced
        for form in [
            self._get_form("legende"),
            self._get_form("legende_filtres"),
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
            )
        )

    def _get_max_displayed_acteurs(self):
        # Hardcoded value taken from dict previously used
        return 25

    @override
    def _get_carte_config(self):
        """Cache the object to avoid repeated queries"""
        return self.get_object()

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


class ProductCarteView(CarteConfigView):
    """This view is used for Produit / Synonyme, the legacy django models
    that were defined prior to Wagtail usage for these pages.

    It will be progressively deprecated until the end of 2025 but
    needs to be maintained for now."""

    filtres_form_class = FiltresFormWithoutSynonyme

    def _get_map_container_id(self):
        # TODO: check if required
        return self.request.GET.get("map_container_id", "carte")

    @override
    def _get_carte_config(self):
        carte_config, _ = CarteConfig.objects.get_or_create(
            slug="product", supprimer_branding=True
        )
        return carte_config

    @override
    def _get_max_displayed_acteurs(self):
        # Hardcoded value taken from dict previously used
        return 25
