import logging

from django.db.models import Q
from django.views.generic import DetailView

from qfdmo.models import CarteConfig, GroupeAction
from qfdmo.views.adresses import CarteSearchActeursView

logger = logging.getLogger(__name__)


class CustomCarteView(DetailView, CarteSearchActeursView):
    model = CarteConfig

    def _get_groupe_actions(self):
        # TODO: cache
        ids = (
            self.get_object()
            .groupe_action_config.all()
            .values_list("groupe_action", flat=True)
        )
        return GroupeAction.objects.filter(id__in=ids)

    def _set_action_list(self, *args, **kwargs):
        actions = self._get_groupe_actions()
        return actions

    def _set_action_displayed(self, *args, **kwargs):
        actions = self._get_groupe_actions()
        return actions

    def _get_selected_action_code(self, *args, **kwargs):
        return self._set_action_list()

    def _compile_acteurs_queryset(self, *args, **kwargs):
        filters, excludes = super()._compile_acteurs_queryset(*args, **kwargs)

        acteur_types_to_filter = (
            self.get_object()
            .groupe_action_config.all()
            .values_list("acteur_type", flat=True)
        )
        if acteur_types_to_filter:
            filters &= Q(acteur_type__in=acteur_types_to_filter)

        if sous_categorie_filter := self.get_object().sous_categorie_objet:
            filters &= Q(
                proposition_services__sous_categories=sous_categorie_filter.first().id,
            )

        return filters, excludes

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        # Action to display and check
        action_displayed = self._set_action_displayed()
        initial["action_displayed"] = "|".join([a.code for a in action_displayed])

        action_list = self._set_action_list(action_displayed)
        initial["action_list"] = "|".join([a.code for a in action_list])

        if self.is_carte:
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
