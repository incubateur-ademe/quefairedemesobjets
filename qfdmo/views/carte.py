import logging

from django.db.models import Q
from django.views.generic import DetailView

from qfdmo.models import CarteConfig
from qfdmo.views.adresses import CarteSearchActeursView

logger = logging.getLogger(__name__)


class CustomCarteView(DetailView, CarteSearchActeursView):
    model = CarteConfig

    @property
    def groupe_actions(self):
        # TODO: cache
        return self.get_object().groupe_action.all().order_by("order")

    def _set_action_list(self, *args, **kwargs):
        return self.groupe_actions

    def _set_action_displayed(self, *args, **kwargs):
        return self.groupe_actions

    def _get_selected_action_code(self, *args, **kwargs):
        return self.groupe_actions

    def get_cached_groupe_action_with_displayed_actions(self, *args, **kwargs):
        return [
            [groupe_action, groupe_action.actions.all()]
            for groupe_action in self.groupe_actions
        ]

    def _grouped_action_from(self, *args, **kwargs):
        return [
            "|".join(groupe_action.actions.all().values_list("code", flat=True))
            for groupe_action in self.get_object().groupe_action.all()
        ]

    def _compile_acteurs_queryset(self, *args, **kwargs):
        filters, excludes = super()._compile_acteurs_queryset(*args, **kwargs)

        # acteur_types_to_filter = (
        #     self.get_object()
        #     .groupe_action_config.all()
        #     .values_list("acteur_type", flat=True)
        # )
        # if acteur_types_to_filter:
        #     filters &= Q(acteur_type__in=acteur_types_to_filter)

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
