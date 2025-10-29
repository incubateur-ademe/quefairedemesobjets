import logging
from typing import Any

from django.conf import settings
from django.db.models import Q
from django.forms import Form
from django.utils.functional import cached_property
from django.views.generic import DetailView

from qfdmo.forms import ActionDirectionForm, CarteForm, ViewModeForm
from qfdmo.models import CarteConfig
from qfdmo.views.adresses import SearchActeursView

logger = logging.getLogger(__name__)


class CarteSearchActeursView(SearchActeursView):
    is_carte = True
    template_name = "ui/pages/carte.html"
    form_class = CarteForm
    forms = {"view_mode": ViewModeForm}

    def get_forms(self) -> dict[str, Form]:
        bounded_forms = {}
        for key, FormCls in self.forms.items():
            if self.request.method == "POST":
                form = FormCls(self.request.POST)
            elif self.request.method == "GET" and set(self.request.GET.keys()) & set(
                FormCls.base_fields.keys()
            ):
                # We instantiate the form only if the request contains fields that are
                # defined on the form.
                form = FormCls(self.request.GET)
            else:
                form = FormCls()

            # Call is_valid to bound form
            form.is_valid()
            bounded_forms[key] = form

        return bounded_forms

    def _get_direction(self):
        action_direction_form = ActionDirectionForm(self.request.GET)
        return action_direction_form["direction"].value()

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        action_displayed = self._set_action_displayed()
        grouped_action_choices = self._get_grouped_action_choices(action_displayed)
        actions_to_select = self._get_selected_action()
        initial["grouped_action"] = self._grouped_action_from(
            grouped_action_choices, actions_to_select
        )
        # TODO : refacto forms, merge with grouped_action field
        initial["legend_grouped_action"] = initial["grouped_action"]

        initial["action_list"] = "|".join(
            [a for ga in initial["grouped_action"] for a in ga.split("|")]
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = self.get_forms()
        context.update(
            is_carte=True,
            forms=forms,
            map_container_id="carte",
            mode_liste=forms["view_mode"]["view"].value()
            == ViewModeForm.ViewModeSegmentedControlChoices.LISTE,
        )
        return context

        return context

    def _get_selected_action_ids(self):
        return [a.id for a in self._get_selected_action()]

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

    @cached_property
    def groupe_actions(self):
        # TODO: cache
        return self.get_object().groupe_action.all().order_by("order")

    def _set_action_list(self, *args, **kwargs):
        if self.groupe_actions:
            return self.groupe_actions
        return super()._set_action_list(*args, **kwargs)

    def _set_action_displayed(self, *args, **kwargs):
        if self.groupe_actions:
            return self.groupe_actions

        return super()._set_action_displayed(*args, **kwargs)

    def _get_selected_action_code(self, *args, **kwargs):
        if self.groupe_actions:
            return self.groupe_actions

        return super()._get_selected_action_code(*args, **kwargs)

    def get_cached_groupe_action_with_displayed_actions(self, *args, **kwargs):
        if self.groupe_actions:
            return [
                [groupe_action, groupe_action.actions.all()]
                for groupe_action in self.groupe_actions
            ]
        else:
            return super().get_cached_groupe_action_with_displayed_actions(
                *args, **kwargs
            )

    def _grouped_action_from(self, *args, **kwargs):
        if self.groupe_actions:
            return [
                "|".join(groupe_action.actions.all().values_list("code", flat=True))
                for groupe_action in self.groupe_actions
            ]
        return super()._grouped_action_from(*args, **kwargs)

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
