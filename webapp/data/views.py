import json
import logging

from data.forms import SuggestionGroupeStatusForm
from data.models.suggestion import (
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.models.suggestions.source import (
    SuggestionGroupeTypeSource,
    SuggestionSourceModel,
    _suggestion_unitaires_to_suggestion_source_model,
)
from data.models.utils import prepare_acteur_data_with_location
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import FormView, View
from qfdmo.models.acteur import Acteur, ActeurStatus, DisplayedActeur, RevisionActeur

logger = logging.getLogger(__name__)


def get_context_from_suggestion_groupe_type_source(
    suggestion_groupe: SuggestionGroupe,
) -> dict:
    """
    Serialize a SuggestionGroupe into a SuggestionGroupeTypeSource and
    return a template context dict with the ComparisonTable.

    Returns a dict with:
        - suggestion_groupe: the SuggestionGroupe instance
        - identifiant_unique: the acteur identifier
        - comparison_table: a ComparisonTable Pydantic model
        - suggestion_groupe_type_source: the SuggestionGroupeTypeSource instance
        - acteur, revision_acteur, parent_revision_acteur (for non-SOURCE_AJOUT)
    """
    sg_type_source = SuggestionGroupeTypeSource.from_suggestion_groupe(
        suggestion_groupe
    )

    context: dict = {
        "suggestion_groupe": suggestion_groupe,
        "identifiant_unique": sg_type_source.identifiant_unique,
        "suggestion_groupe_type_source": sg_type_source,
        "comparison_table": sg_type_source.to_comparison_table(),
        "acteur": sg_type_source.acteur,
        "revision_acteur": sg_type_source.revision_acteur,
        "parent_revision_acteur": sg_type_source.parent_revision_acteur,
    }

    return context


def update_suggestion_groupe(
    suggestion_groupe: SuggestionGroupe,
    suggestion_modele: str,
    fields_values: dict,
    fields_groups: list[tuple],
) -> tuple[bool, dict | None]:
    """
    for each fields to update

    if there is a suggestion that modify already this field
      -> update this modification
    if there is no acteur nor suggestion that modify this field
      -> create a suggestion of modification
    if there is an acteur (according to the model)
       and that the field is different from the acteur value
      -> create a suggestion of modification
    """

    def _validate_proposed_updates(values_to_update: dict, fields_values: dict) -> dict:
        """
        Check if the proposed updates are valid using SuggestionSourceType
        Returns a dictionary of errors (empty if valid)
        """
        # Validate the RevisionActeur with the proposed values
        if "longitude" in values_to_update or "latitude" in values_to_update:
            for coord_field in ["longitude", "latitude"]:
                try:
                    values_to_update[coord_field] = values_to_update.get(
                        coord_field,
                        fields_values.get(coord_field, "0.0"),
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"ValueError for {coord_field}: {e}")
                    return {coord_field: f"{coord_field} must be a float: {e}"}

        try:
            values_to_update = prepare_acteur_data_with_location(values_to_update)
        except (ValueError, KeyError) as e:
            logger.warning(f"ValueError for : {e}")
            return {
                "latitude": f"latitude must be a float: {e}",
                "longitude": f"longitude must be a float: {e}",
            }
        try:
            revision_acteur = RevisionActeur(
                **prepare_acteur_data_with_location(values_to_update)
            )
            # Statut should be set because Django don't set it automatically even
            # if the field has a default value
            if not revision_acteur.statut:
                revision_acteur.statut = ActeurStatus.ACTIF
            revision_acteur.full_clean()
        except ValidationError as e:
            logger.warning(f"RevisionActeur is not valid: {e}")
            return e.error_dict
        except TypeError as e:
            logger.warning(f"RevisionActeur is not valid: {e}")
            return {"error": str(e)}

        return {}

    if suggestion_modele not in ["Acteur", "RevisionActeur", "ParentRevisionActeur"]:
        raise ValueError(f"Invalid suggestion_modele: {suggestion_modele}")

    # Filter fields_values to only include fields that are reportable on the
    # suggestion_modele
    if suggestion_modele == "RevisionActeur":
        fields_values = {
            field: value
            for field, value in fields_values.items()
            if field
            not in SuggestionSourceModel.get_not_reportable_on_revision_fields()
        }
    elif suggestion_modele == "ParentRevisionActeur":
        fields_values = {
            field: value
            for field, value in fields_values.items()
            if field not in SuggestionSourceModel.get_not_reportable_on_parent_fields()
        }

    acteur = (
        suggestion_groupe.get_acteur_or_none()
        if suggestion_modele == "Acteur"
        else (
            suggestion_groupe.get_revision_acteur_or_none()
            if suggestion_modele == "RevisionActeur"
            else suggestion_groupe.get_parent_revision_acteur_or_none()
        )
    )
    identifiant_unique = (
        (acteur and acteur.identifiant_unique)
        or suggestion_groupe.acteur_id
        or suggestion_groupe.get_identifiant_unique_from_suggestion_unitaires()
    )

    if not identifiant_unique:
        raise ValueError("identifiant_unique is missing")

    suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())
    # Flatten and convert to SuggestionSourceModel
    revision_suggestion_unitaire_by_field = (
        _suggestion_unitaires_to_suggestion_source_model(
            suggestion_unitaires, suggestion_modele
        )
    )

    values_to_update = {
        field: value
        for field, value in fields_values.items()
        # if exists a suggestion that modify already this field, update this
        # modification
        if getattr(revision_suggestion_unitaire_by_field, field, None) is not None
        # if there is no acteur nor suggestion that modify this field, create a
        # suggestion of modification
        or not acteur
        # if there is an acteur (according to the model) and that the field is
        # different from the acteur value, create a suggestion of modification
        or (acteur and getattr(acteur, field, None) != value)
    }

    # complete fields_groups with value of the other field in field_groups
    # if it is not in values_to_update
    new_values_to_update = {}
    for field in values_to_update.keys():
        # find field_group that contains field
        field_group = next(
            (field_group for field_group in fields_groups if field in field_group), None
        )
        if field_group and len(field_group) > 1:
            for other_field in field_group:
                if other_field == field:
                    continue
                if other_field not in values_to_update.keys():
                    # set the value by default of the other field
                    if (
                        getattr(revision_suggestion_unitaire_by_field, other_field)
                        is not None
                    ):
                        new_values_to_update[other_field] = getattr(
                            revision_suggestion_unitaire_by_field, other_field
                        )
                    elif acteur:
                        new_values_to_update[other_field] = getattr(acteur, other_field)
    values_to_update.update(new_values_to_update)

    # Validate proposed updates
    try:
        if errors := _validate_proposed_updates(values_to_update, fields_values):
            return False, errors
    except Exception as e:
        logger.warning(f"Error validating proposed updates: {e}")
        return False, {"error": str(e)}

    # Create or update SuggestionUnitaire objects
    for fields in fields_groups:
        if any(field in values_to_update for field in fields):
            suggestion_unitaire, _ = SuggestionUnitaire.objects.get_or_create(
                suggestion_groupe=suggestion_groupe,
                champs=fields,
                suggestion_modele=suggestion_modele,
                defaults={
                    "acteur_id": (
                        identifiant_unique if suggestion_modele == "Acteur" else None
                    ),
                    "revision_acteur_id": (
                        identifiant_unique
                        if suggestion_modele == "RevisionActeur"
                        else None
                    ),
                    "parent_revision_acteur_id": (
                        identifiant_unique
                        if suggestion_modele == "ParentRevisionActeur"
                        else None
                    ),
                },
            )
            suggestion_unitaire.valeurs = [
                values_to_update.get(field, "") for field in fields
            ]
            suggestion_unitaire.save()

    return True, None


class SuggestionGroupeStatusView(LoginRequiredMixin, FormView):
    form_class = SuggestionGroupeStatusForm

    def get_success_url(self):
        return reverse_lazy(
            "data:suggestion_groupe",
            kwargs={"suggestion_groupe_id": self.kwargs["suggestion_groupe_id"]},
        )

    def form_valid(self, form):
        suggestion_groupe = get_object_or_404(
            SuggestionGroupe.objects,
            id=self.kwargs["suggestion_groupe_id"],
        )
        action = form.cleaned_data["action"]
        if action == "validate":
            suggestion_groupe.statut = SuggestionStatut.ATRAITER
        elif action == "reject":
            suggestion_groupe.statut = SuggestionStatut.REJETEE
        elif action == "to_process":
            suggestion_groupe.statut = SuggestionStatut.AVALIDER
        suggestion_groupe.save()

        return super().form_valid(form)


class SuggestionGroupeView(LoginRequiredMixin, View):
    template_name = "data/_partials/suggestion_groupe_refresh_stream.html"

    def _manage_tab_in_context(
        self,
        *,
        tab: str | None,
        suggestion_groupe: SuggestionGroupe,
        acteur: Acteur | None | None,
        revision_acteur: RevisionActeur | None,
        parent_revision_acteur: RevisionActeur | None,
    ):

        def _get_displayed_acteur_uuid(acteur, revision_acteur, parent_revision_acteur):
            final_acteur = parent_revision_acteur or revision_acteur or acteur
            if final_acteur:
                displayed_acteur = DisplayedActeur.objects.filter(
                    identifiant_unique=final_acteur.identifiant_unique
                ).first()
                return displayed_acteur.uuid if displayed_acteur else None
            return None

        suggestion_unitaires = suggestion_groupe.suggestion_unitaires.all()
        acteur_suggestion_unitaires_latlong = next(
            (
                suggestion_unitaire
                for suggestion_unitaire in suggestion_unitaires
                if suggestion_unitaire.suggestion_modele == "Acteur"
                and suggestion_unitaire.champs == ["latitude", "longitude"]
            ),
            None,
        )
        revision_acteur_suggestion_unitaires_latlong = next(
            (
                suggestion_unitaire
                for suggestion_unitaire in suggestion_unitaires
                if suggestion_unitaire.suggestion_modele == "RevisionActeur"
                and suggestion_unitaire.champs == ["latitude", "longitude"]
            ),
            None,
        )
        parent_revision_acteur_suggestion_unitaires_latlong = next(
            (
                suggestion_unitaire
                for suggestion_unitaire in suggestion_unitaires
                if suggestion_unitaire.suggestion_modele == "ParentRevisionActeur"
                and suggestion_unitaire.champs == ["latitude", "longitude"]
            ),
            None,
        )
        context = {"tab": tab}
        if tab == "acteur":
            context["uuid"] = _get_displayed_acteur_uuid(
                acteur, revision_acteur, parent_revision_acteur
            )
        points = []
        if tab == "localisation":
            # Pinpoint of the acteur as it is saved in the database
            # Not editable by the user (draggable is False)
            if acteur and acteur.latitude and acteur.longitude:
                points.append(
                    {
                        "latitude": float(acteur.latitude),
                        "longitude": float(acteur.longitude),
                        "color": "grey",
                        "key": "Origin",
                        "draggable": False,
                    }
                )
            # Pinpoint of the acteur as it is suggested by the source
            # Not editable by the user (draggable is False)
            if acteur_suggestion_unitaires_latlong:
                points.append(
                    {
                        "latitude": float(
                            acteur_suggestion_unitaires_latlong.valeurs[0]
                        ),
                        "longitude": float(
                            acteur_suggestion_unitaires_latlong.valeurs[1]
                        ),
                        "color": "green",
                        "key": "Suggestion",
                        "text": "A",
                        "draggable": False,
                    }
                )
            # Pinpoint of the correction
            # From suggestion over the correction suggestion if exists
            # Then from Correction itself if exists
            # Editable by the user (draggable is True)
            if (
                revision_acteur
                and revision_acteur.latitude
                and revision_acteur.longitude
            ) or revision_acteur_suggestion_unitaires_latlong:
                latitude = (
                    revision_acteur_suggestion_unitaires_latlong.valeurs[0]
                    if revision_acteur_suggestion_unitaires_latlong
                    else revision_acteur.latitude
                )
                longitude = (
                    revision_acteur_suggestion_unitaires_latlong.valeurs[1]
                    if revision_acteur_suggestion_unitaires_latlong
                    else revision_acteur.longitude
                )
                points.append(
                    {
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                        "color": "blue",
                        "key": "RevisionActeur",
                        "text": "▶️",
                        "draggable": True,
                    }
                )
            # Pinpoint of the parent
            # From suggestion over the parent suggestion if exists
            # Then from Parent itself if exists
            # Editable by the user (draggable is True)
            if parent_revision_acteur_suggestion_unitaires_latlong or (
                parent_revision_acteur
                and parent_revision_acteur.latitude
                and parent_revision_acteur.longitude
            ):
                latitude = (
                    parent_revision_acteur_suggestion_unitaires_latlong.valeurs[0]
                    if parent_revision_acteur_suggestion_unitaires_latlong
                    else parent_revision_acteur.latitude
                )
                longitude = (
                    parent_revision_acteur_suggestion_unitaires_latlong.valeurs[1]
                    if parent_revision_acteur_suggestion_unitaires_latlong
                    else parent_revision_acteur.longitude
                )
                points.append(
                    {
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                        "color": "red",
                        "key": "ParentRevisionActeur",
                        "text": "⏩",
                        "draggable": True,
                    }
                )

        if points:
            context["localisation"] = {
                "points": points,
            }

        return context

    def get(self, request, suggestion_groupe_id):
        suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)

        context = get_context_from_suggestion_groupe_type_source(suggestion_groupe)
        to_add_in_context = self._manage_tab_in_context(
            tab=request.GET.get("tab", request.POST.get("tab", None)),
            suggestion_groupe=suggestion_groupe,
            acteur=context["acteur"] if "acteur" in context else None,
            revision_acteur=(
                context["revision_acteur"] if "revision_acteur" in context else None
            ),
            parent_revision_acteur=(
                context["parent_revision_acteur"]
                if "parent_revision_acteur" in context
                else None
            ),
        )
        context.update(to_add_in_context)

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )

    def post(self, request, suggestion_groupe_id):
        suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)

        fields_values_payload = request.POST.get("fields_values", "{}")
        fields_groups_payload = request.POST.get("fields_groups", "{}")
        suggestion_modele_payload = request.POST.get("suggestion_modele")
        if suggestion_modele_payload not in [
            "RevisionActeur",
            "ParentRevisionActeur",
        ]:
            return HttpResponseBadRequest(
                "suggestion_modele must be RevisionActeur or ParentRevisionActeur"
            )

        try:
            fields_values = (
                json.loads(fields_values_payload) if fields_values_payload else {}
            )
            fields_groups = (
                json.loads(fields_groups_payload) if fields_groups_payload else []
            )
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Payload fields_list invalide")
        _, errors = update_suggestion_groupe(
            suggestion_groupe, suggestion_modele_payload, fields_values, fields_groups
        )

        context = get_context_from_suggestion_groupe_type_source(suggestion_groupe)
        to_add_in_context = self._manage_tab_in_context(
            tab=request.GET.get("tab", request.POST.get("tab", None)),
            suggestion_groupe=suggestion_groupe,
            acteur=context["acteur"] if "acteur" in context else None,
            revision_acteur=(
                context["revision_acteur"] if "revision_acteur" in context else None
            ),
            parent_revision_acteur=(
                context["parent_revision_acteur"]
                if "parent_revision_acteur" in context
                else None
            ),
        )
        context.update(to_add_in_context)
        context["errors"] = errors if errors else {}
        if errors:
            sg_type_source = context["suggestion_groupe_type_source"]
            context["comparison_table"] = sg_type_source.to_comparison_table(
                errors=errors
            )

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )
