import logging
from typing import Any, TypedDict, override

from django.conf import settings
from django.db.models import Q
from django.forms import Form
from django.views.generic import DetailView

from core.constants import MAP_CONTAINER_ID
from qfdmd.models import Produit
from qfdmo.forms import (
    ActionDirectionForm,
    AutoSubmitLegendeForm,
    CarteForm,
    FiltresForm,
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
    forms: CarteForms = {
        "view_mode": {
            "form": ViewModeForm,
            "prefix": "view_mode",
        },
        "filtres": {
            "form": FiltresForm,
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

    def __init__(self, **kwargs):
        # TODO: check that linked forms have exactly the same fields
        super().__init__(**kwargs)

    def _generate_prefix(self, prefix: str) -> str:
        try:
            id = self.request.GET[MAP_CONTAINER_ID]
            return f"{id}_{prefix}"
        except (KeyError, AttributeError):
            return prefix

    def _get_forms(self) -> CarteFormsInstance:
        form_instances: CarteFormsInstance = {}
        for key, form_config in self.forms.items():
            if self.request.method == "POST":
                data = self.request.POST
            else:
                data = self.request.GET

            prefix = self._generate_prefix(form_config["prefix"])
            # carte_legende-nom_du_champ
            form = form_config["form"](
                data, prefix=prefix, carte_config=self._get_carte_config()
            )
            if not form.is_valid():
                for other_prefix in form_config.get("other_prefixes_to_check", []):
                    other_prefix = self._generate_prefix(other_prefix)
                    other_form = form_config["form"](
                        data, prefix=other_prefix, carte_config=self._get_carte_config()
                    )
                    if other_form.is_valid():
                        form = other_form
                        break

            form_instances[key] = form

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

    @property
    def carte_config(self) -> CarteConfig | None:
        return self._get_carte_config()

    def _get_max_displayed_acteurs(self):
        if self.carte_config and self.carte_config.nombre_d_acteurs_affiches:
            return self.carte_config.nombre_d_acteurs_affiches
        if self.request.GET.get("limit", "").isnumeric():
            return int(self.request.GET.get("limit"))
        return settings.CARTE_MAX_SOLUTION_DISPLAYED

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = self._get_forms()
        mode_liste = (
            forms["view_mode"]["view"].value()
            == ViewModeForm.ViewModeSegmentedControlChoices.LISTE
        )

        context.update(
            is_carte=True,
            forms=forms,
            map_container_id=self._get_map_container_id(),
            mode_liste=mode_liste,
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

        return (
            Action.objects.filter(groupe_action__id__in=groupe_action_ids)
            .only("id")
            .values_list("id", flat=True)
        )

    def _get_sous_categorie_ids(self) -> list[int]:
        synonyme_id = self._get_field_value_for("filtres", "synonyme")
        if not synonyme_id:
            return []

        return Produit.objects.filter(synonymes__id__in=[synonyme_id]).values_list(
            "sous_categories__id", flat=True
        )


class ProductCarteView(CarteSearchActeursView):
    """This view is used for Produit / Synonyme, the legacy django models
    that were defined prior to Wagtail usage for these pages.

    It will be progressively deprecated until the end of 2025 but
    needs to be maintained for now."""

    def _get_map_container_id(self):
        # TODO: check if required
        return self.request.GET.get("map_container_id", "carte")

    def _get_carte_config(self):
        carte_config, _ = CarteConfig.objects.get_or_create(
            slug="product", supprimer_branding=True
        )
        return carte_config

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CarteConfigView(DetailView, CarteSearchActeursView):
    model = CarteConfig
    context_object_name = "carte_config"

    @override
    def _get_carte_config(self):
        return self.object

    def get_sous_categorie_filter(self):
        sous_categories_from_request = list(
            filter(
                None, self.request.GET.getlist(CarteConfig.SOUS_CATEGORIE_QUERY_PARAM)
            )
        )
        if sous_categories_from_request:
            return sous_categories_from_request

        return self.get_object().sous_categorie_objet.all().values_list("id", flat=True)

    def _compile_acteurs_queryset(self, *args, **kwargs):
        filters, excludes = super()._compile_acteurs_queryset(*args, **kwargs)

        if source_filter := self.get_object().source.all():
            filters &= Q(source__in=source_filter)

        if label_filter := self.get_object().label_qualite.all():
            filters &= Q(labels__in=label_filter)

        if acteur_type_filter := self.get_object().acteur_type.all():
            filters &= Q(acteur_type__in=acteur_type_filter)

        if sous_categorie_filter := self.get_sous_categorie_filter():
            filters &= Q(
                proposition_services__sous_categories__id__in=sous_categorie_filter,
            )

        if groupe_action_filter := self.get_object().groupe_action.all():
            action_ids = list(
                groupe_action_filter.values_list("actions__id", flat=True)
            )
            filters &= Q(
                proposition_services__action_id__in=action_ids,
            )
        return filters, excludes
