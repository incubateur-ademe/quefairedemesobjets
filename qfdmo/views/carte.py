import logging

from django.db.models import Q
from django.utils.functional import cached_property
from django.views.generic import DetailView

from qfdmo.forms import CarteForm, DisplayedActeursForm
from qfdmo.models import CarteConfig
from qfdmo.views.adresses import SearchActeursView

logger = logging.getLogger(__name__)


class CarteSearchActeursView(SearchActeursView):
    is_carte = True
    template_name = "qfdmo/carte.html"
    form_class = CarteForm

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
        self.displayed_acteur_form = DisplayedActeursForm(self.request.GET)

        if not self.displayed_acteur_form.is_valid():
            logger.error(f"Form is valid {self.displayed_acteur_form=}")

        context = super().get_context_data(**kwargs)
        context.update(
            is_carte=True,
            map_container_id="carte",
            displayed_acteur_form=self.displayed_acteur_form,
        )

        return context

    def _get_selected_action_ids(self):
        return [a.id for a in self._get_selected_action()]

    def get_sous_categories_ids(self):
        if sous_categories := self.displayed_acteur_form.cleaned_data.get(
            "sous_categories"
        ):
            return sous_categories.values_list("pk", flat=True)

        return super().get_sous_categories_ids()


class ProductCarteView(CarteSearchActeursView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carte_config, _ = CarteConfig.objects.get_or_create(
            slug="product", no_branding=True
        )
        context.update(
            carte_config=carte_config,
            map_container_id=self.request.GET.get("map_container_id", "carte"),
        )
        return context


class CustomCarteView(DetailView, CarteSearchActeursView):
    model = CarteConfig
    context_object_name = "carte_config"

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

    def _compile_acteurs_queryset(self, *args, **kwargs):
        filters, excludes = super()._compile_acteurs_queryset(*args, **kwargs)

        if source_filter := self.get_object().source.all():
            filters &= Q(source__in=source_filter)

        if label_filter := self.get_object().label.all():
            filters &= Q(labels__in=label_filter)

        if acteur_type_filter := self.get_object().acteur_type.all():
            filters &= Q(acteur_type__in=acteur_type_filter)

        if sous_categorie_filter := self.get_object().sous_categorie_objet.all():
            filters &= Q(
                proposition_services__sous_categories__in=sous_categorie_filter,
            )

        if groupe_action_filter := self.get_object().groupe_action.all():
            action_ids = list(
                groupe_action_filter.values_list("actions__id", flat=True)
            )
            filters &= Q(
                proposition_services__action_id__in=action_ids,
            )
        return filters, excludes
