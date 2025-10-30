import logging
from typing import Any, Optional, Type, TypedDict

from django.conf import settings
from django.db.models import Q
from django.forms import Form
from django.views.generic import DetailView

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


class CarteForms(TypedDict):
    view_mode: Type[ViewModeForm]
    # ess etc desktop / mobile : tout le temps
    filtres: Type[FiltresForm]
    # gestes desktop : carte
    legende: Type[LegendeForm]
    # desktop : mode liste
    legende_filtres: Type[LegendeForm]


class CarteFormsInstance(TypedDict):
    view_mode: Optional[ViewModeForm]
    filtres: Optional[FiltresForm]
    legende: Optional[LegendeForm]
    legende_filtres: Optional[LegendeForm]


class CarteSearchActeursView(SearchActeursView):
    is_carte = True
    template_name = "ui/pages/carte.html"
    form_class = CarteForm
    forms: CarteForms = {
        "view_mode": ViewModeForm,
        "filtres": FiltresForm,
        "legende": AutoSubmitLegendeForm,
        "legende_filtres": LegendeForm,
    }

    def _generate_prefix(self, prefix: str) -> str:
        try:
            id = self.request.GET["map_container_id"]
            return f"{id}-{prefix}"
        except (KeyError, AttributeError):
            return prefix

    def _get_forms(self) -> CarteFormsInstance:
        form_instances: CarteFormsInstance = {}
        for key, FormCls in self.forms.items():
            if self.request.method == "POST":
                data = self.request.POST
            else:
                data = self.request.GET

            prefix = self._generate_prefix(key)
            form = FormCls(data, prefix=prefix)
            form_instances[key] = form

        return form_instances

    def _get_form(self, form_name) -> Form | None:
        try:
            return self._get_forms()[form_name]
        except KeyError:
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
            return label in self._get_form("filtres")["label"].value()
        except (TypeError, KeyError):
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = self._get_forms()
        context.update(
            is_carte=True,
            forms=forms,
            map_container_id="carte",
            mode_liste=forms["view_mode"]["view"].value()
            == ViewModeForm.ViewModeSegmentedControlChoices.LISTE,
        )
        return context

    def _get_action_ids(self) -> list[str]:
        groupe_action_ids = self._get_form("legende")["groupe_action"].value()
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

    def _get_max_displayed_acteurs(self):
        if self.request.GET.get("limit", "").isnumeric():
            return int(self.request.GET.get("limit"))
        return settings.CARTE_MAX_SOLUTION_DISPLAYED


class ProductCarteView(CarteSearchActeursView):
    """This view is used for Produit / Synonyme, the legacy django models
    that were defined prior to Wagtail usage for these pages.

    It will be progressively deprecated until the end of 2025 but
    needs to be maintained for now."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carte_config, _ = CarteConfig.objects.get_or_create(
            slug="product", supprimer_branding=True
        )
        context.update(
            carte_config=carte_config,
            map_container_id=self.request.GET.get("map_container_id", "carte"),
        )
        return context


class CarteConfigView(DetailView, CarteSearchActeursView):
    model = CarteConfig
    context_object_name = "carte_config"

    def _get_max_displayed_acteurs(self):
        """Standalone Carte view displays more acteurs than the
        embedded one."""
        return settings.CARTE_MAX_SOLUTION_DISPLAYED

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return {
            **super().get_context_data(**kwargs),
            "map_container_id": self.object.pk,
        }

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

        if label_filter := self.get_object().label.all():
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
