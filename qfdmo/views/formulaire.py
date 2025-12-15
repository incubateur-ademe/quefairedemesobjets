from typing import Any, cast

from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet
from django.forms import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.utils.html import mark_safe

from qfdmo.forms import ActionDirectionForm, DigitalActeurForm, FormulaireForm
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import Action, GroupeAction, get_action_instances
from qfdmo.views.adresses import AbstractSearchActeursView


class FormulaireSearchActeursView(AbstractSearchActeursView):
    """Affiche le formulaire utilisé sur epargnonsnosressources.gouv.fr
    Cette vue est à considérer en mode maintenance uniquement et ne doit pas être
    modifiée."""

    is_iframe = True
    template_name = "ui/pages/formulaire.html"
    form_class = FormulaireForm

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.digital_acteur_form: DigitalActeurForm = DigitalActeurForm(
            self.request.GET
        )
        self.action_direction_form = ActionDirectionForm(
            self.request.GET,
            initial={"direction": ActionDirectionForm.DirectionChoices.J_AI.value},
        )
        return super().get(request, *args, **kwargs)

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

        # TODO: refacto forms : delete this line
        initial["sous_categorie_objet"] = self.request.GET.get("sous_categorie_objet")
        initial["pas_exclusivite_reparation"] = self.request.GET.get(
            "pas_exclusivite_reparation", True
        )
        # TODO: refacto forms : delete this line
        initial["label_reparacteur"] = self.request.GET.get("label_reparacteur")
        # TODO: refacto forms : delete this line
        initial["bonus"] = self.request.GET.get("bonus")
        # TODO: refacto forms : delete this line
        initial["ess"] = self.request.GET.get("ess")
        # Action to display and check
        action_displayed = self._set_action_displayed()
        initial["action_displayed"] = "|".join([a.code for a in action_displayed])
        initial["sc_id"] = (
            self.request.GET.get("sc_id") if initial["sous_categorie_objet"] else None
        )

        action_list = self._set_action_list(action_displayed)
        initial["action_list"] = "|".join([a.code for a in action_list])
        return initial

    def get_form(self, form_class=None):
        # TODO : vérifier s'il faut récupérer l'implémentation
        #  de SearchActeursView ou pas
        form = super().get_form(form_class)

        action_displayed = self._set_action_displayed() if self.is_carte else None
        grouped_action_choices = (
            self._get_grouped_action_choices(action_displayed)
            if action_displayed
            else None
        )

        form.load_choices(
            self.request,
            grouped_action_choices=grouped_action_choices,
            disable_reparer_option=(
                "reparer" not in form.initial.get("grouped_action", [])
            ),
        )
        return form

    def _set_action_displayed(self) -> list[Action]:
        cached_action_instances = cast(
            list[Action], cache.get_or_set("action_instances", get_action_instances)
        )
        """
        Limit to actions of the direction only in Carte mode
        """
        if direction := self._get_direction():
            if self.is_carte:
                cached_action_instances = [
                    action
                    for action in cached_action_instances
                    if direction in [d.code for d in action.directions.all()]
                ]
        if action_displayed := self.get_data_from_request_or_bounded_form(
            "action_displayed", ""
        ):
            cached_action_instances = [
                action
                for action in cached_action_instances
                if action.code in action_displayed.split("|")
            ]
        # In form mode, only display actions with afficher=True
        # TODO : discuss with epargnonsnosressources if we can remove this condition
        # or set it in get_action_instances
        if not self.is_carte:
            cached_action_instances = [
                action for action in cached_action_instances if action.afficher
            ]
        return cached_action_instances

    def _set_action_list(self, action_displayed: list[Action]) -> list[Action]:
        if action_list := self.get_data_from_request_or_bounded_form("action_list", ""):
            return [
                action
                for action in action_displayed
                if action.code in action_list.split("|")
            ]
        return action_displayed

    def _get_selected_action_code(self):
        """
        Get the action to include in the request
        """
        # FIXME : est-ce possible d'optimiser en accédant au valeur initial du form ?

        # selection from interface
        if self.get_data_from_request_or_bounded_form("grouped_action"):
            return [
                code
                for new_groupe_action in self.get_data_from_request_or_bounded_form(
                    "grouped_action"
                )
                for code in new_groupe_action.split("|")
            ]
        # Selection is not set in interface, get all available from
        # (checked_)action_list
        if self.get_data_from_request_or_bounded_form("action_list"):
            return self.get_data_from_request_or_bounded_form("action_list", "").split(
                "|"
            )
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        if self.get_data_from_request_or_bounded_form("action_displayed"):
            return self.get_data_from_request_or_bounded_form(
                "action_displayed", ""
            ).split("|")
        # return empty array, will search in all actions
        return []

    def _get_selected_action(self) -> list[Action]:
        """
        Get the action to include in the request
        """

        codes = []
        # selection from interface
        if self.request.GET.get("grouped_action"):
            codes = [
                code
                for new_groupe_action in self.request.GET.getlist("grouped_action")
                for code in new_groupe_action.split("|")
            ]
        # Selection is not set in interface, get all available from
        # (checked_)action_list
        elif action_list := self.cleaned_data.get("action_list"):
            # TODO : effet de bord si la list des action n'est pas cohérente avec
            # les actions affichées
            # il faut collecté les actions coché selon les groupes d'action
            codes = action_list.split("|")
        # Selection is not set in interface, defeult checked action list is not set
        # get all available from action_displayed
        elif action_displayed := self.cleaned_data.get("action_displayed"):
            codes = action_displayed.split("|")
        # return empty array, will search in all actions

        # Cast needed because of the cache
        cached_action_instances = cast(
            list[Action], cache.get_or_set("action_instances", get_action_instances)
        )
        actions = (
            [a for a in cached_action_instances if a.code in codes]
            if codes
            else cached_action_instances
        )
        if direction := self._get_direction():
            actions = [
                a for a in actions if direction in [d.code for d in a.directions.all()]
            ]
        return actions

    def _get_grouped_action_choices(
        self, action_displayed: list[Action]
    ) -> list[list[str]]:
        """Generate a list of choices for form field
        used in legend"""
        # Generate a tuple of (code, libelle) used in the frontend.
        # The libelle is automatically picked up by django templating
        # when generating the form.
        grouped_action_choices = []
        for [
            groupe,
            groupe_displayed_actions,
        ] in self.get_cached_groupe_action_with_displayed_actions(action_displayed):
            libelle = ""
            if groupe.icon:
                libelle = render_to_string(
                    "ui/forms/widgets/groupe_action_label.html",
                    {
                        "groupe_action": groupe,
                        "libelle": groupe.get_libelle_from(groupe_displayed_actions),
                    },
                )

            code = "|".join([a.code for a in groupe_displayed_actions])
            grouped_action_choices.append([code, mark_safe(libelle)])
        return grouped_action_choices

    def _grouped_action_from(
        self, grouped_action_choices: list[list[str]], action_list: list[Action]
    ) -> list[str]:
        return [
            groupe_option[0]
            for groupe_option in grouped_action_choices
            if set(groupe_option[0].split("|")) & set([a.code for a in action_list])
        ]

    def _get_direction(self):
        return self.action_direction_form["direction"].value()

    def _get_ess(self):
        return self.get_data_from_request_or_bounded_form("ess")

    def _get_label_reparacteur(self):
        return self.get_data_from_request_or_bounded_form("label_reparacteur")

    def _get_bonus(self):
        return self.get_data_from_request_or_bounded_form("bonus")

    def _get_pas_exclusivite_reparation(self) -> bool:
        return self.get_data_from_request_or_bounded_form("pas_exclusivite_reparation")

    def _get_sous_categorie_ids(self) -> list[int]:
        if id := self.get_data_from_request_or_bounded_form("sc_id"):
            return [id]
        return []

    def _get_action_ids(self) -> list[str]:
        return self._get_selected_action_ids()

    def _get_bounding_box(self) -> str | None:
        """Get bounding_box from request or form"""
        return cast(
            str | None, self.get_data_from_request_or_bounded_form("bounding_box")
        )

    def _get_longitude(self):
        return self.get_data_from_request_or_bounded_form("longitude")

    def _get_latitude(self):
        return self.get_data_from_request_or_bounded_form("latitude")

    def _should_show_results(self):
        initial = self.get_initial()
        return (
            initial.get("adresse")
            or initial.get("bounding_box")
            or initial.get("epci_codes")
        )

    def _check_if_is_digital(self):
        return (
            self.digital_acteur_form["digital"].value()
            == self.digital_acteur_form.DigitalChoices.DIGITAL.value
        )

    def _get_epci_codes(self) -> list[str]:
        return []

    def _handle_scoped_acteurs(
        self, acteurs: QuerySet[DisplayedActeur], **kwargs
    ) -> tuple[Any, QuerySet[DisplayedActeur]]:
        """
        Handle the scoped acteurs following the order of priority:
        - digital
        - bbox
        - epci_codes
        - user location
        override from parent class to handle digital acteurs
        """

        if self._check_if_is_digital():
            return None, acteurs.digital()
        return super()._build_acteurs_queryset_from_location(acteurs, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self._check_if_is_digital():
            context.update(is_digital=True)

        context.update(
            map_container_id="formulaire",
            action_direction_form=self.action_direction_form,
            digital_acteur_form=self.digital_acteur_form,
            selected_action_codes=self._get_action_codes(),
        )
        return context

    def _get_action_codes(self) -> str:
        """Get selected action codes as a pipe-separated string for use in templates.

        Returns action codes that can be passed to acteur_pinpoint_tag.
        """
        action_list = self.get_action_list()
        if not action_list:
            return ""
        action_codes = [action["code"] for action in action_list]
        return "|".join(action_codes)

    def _get_selected_action_ids(self):
        # TODO: merge this method with the one from CarteSearchActeursView
        # and do not return a list of dict but a queryset instead
        return [a["id"] for a in self.get_action_list()]

    def get_action_list(self) -> list[dict]:
        direction = self._get_direction()
        action_displayed = self._set_action_displayed()
        actions = self._set_action_list(action_displayed)
        if direction:
            actions = [
                a for a in actions if direction in [d.code for d in a.directions.all()]
            ]
        return [model_to_dict(a, exclude=["directions"]) for a in actions]

    def _get_max_displayed_acteurs(self):
        return settings.DEFAULT_MAX_SOLUTION_DISPLAYED

    def get_cached_groupe_action_with_displayed_actions(self, action_displayed):
        # Cast needed because of the cache
        cached_groupe_action_instances = cast(
            QuerySet[GroupeAction],
            cache.get_or_set(
                "groupe_action_instances", self.get_groupe_action_instances
            ),
        )

        # Fetch actions from cache only if they are displayed
        # for the end user
        cached_groupe_action_with_displayed_actions = []
        for cached_groupe in cached_groupe_action_instances:
            if displayed_actions_from_groupe_actions := [
                action
                # TODO : à optimiser avec le cache
                for action in cached_groupe.actions.all().order_by(  # type: ignore
                    "order"
                )
                if action in action_displayed
            ]:
                cached_groupe_action_with_displayed_actions.append(
                    [cached_groupe, displayed_actions_from_groupe_actions]
                )
        return cached_groupe_action_with_displayed_actions

    def get_groupe_action_instances(self) -> QuerySet[GroupeAction]:
        return GroupeAction.objects.prefetch_related("actions").order_by("order")

    def get_reparer_action_id(self) -> int:
        try:
            return [
                action for action in get_action_instances() if action.code == "reparer"
            ][0].id
        except IndexError:
            raise Exception("Action 'Réparer' not found")

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
