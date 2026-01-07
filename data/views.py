import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import FormView, View
from more_itertools import flatten

from data.forms import SuggestionGroupeStatusForm
from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorteSerializer,
    SuggestionGroupe,
    SuggestionSourceType,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.models.utils import data_latlong_to_location
from qfdmo.models.acteur import RevisionActeur

logger = logging.getLogger(__name__)


def _build_serializer_common_fields(suggestion_groupe: SuggestionGroupe) -> dict:
    """Build common fields for SuggestionCohorteSerializer"""
    return {
        "id": suggestion_groupe.id,
        "suggestion_cohorte": suggestion_groupe.suggestion_cohorte,
        "statut": suggestion_groupe.get_statut_display(),
        "action": suggestion_groupe.suggestion_cohorte.type_action,
    }


def _flatten_suggestion_unitaires(
    suggestion_unitaires: dict[tuple, list],
) -> dict:
    return {
        k: v
        for k, v in zip(
            flatten(suggestion_unitaires.keys()),
            flatten(suggestion_unitaires.values()),
        )
    }


def _get_ordered_fields_groups(
    acteur_suggestion_unitaires: dict,
    acteur_overridden_by_suggestion_unitaires: dict | None = None,
) -> list[tuple]:
    """Get ordered fields groups using SuggestionSourceType validation"""
    fields_groups = list(
        set(acteur_suggestion_unitaires.keys())
        | set(
            acteur_overridden_by_suggestion_unitaires.keys()
            if acteur_overridden_by_suggestion_unitaires
            else set()
        )
    )

    # Validate using SuggestionSourceType
    ordered_fields = SuggestionSourceType.get_ordered_fields()
    if any(fields not in ordered_fields for fields in fields_groups):
        raise ValueError(
            f"""fields in fields_groups are not in ORDERED_FIELDS:
                        {fields_groups=}
                        {ordered_fields=}"""
        )
    return [fields for fields in ordered_fields if fields in fields_groups]


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
                    fields_values.get(coord_field, {}).get("displayed_value", ""),
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"ValueError for {coord_field}: {e}")
                return {coord_field: f"{coord_field} must be a float: {e}"}

    try:
        values_to_update = data_latlong_to_location(values_to_update)
    except (ValueError, KeyError) as e:
        logger.warning(f"ValueError for : {e}")
        return {
            "latitude": f"latitude must be a float: {e}",
            "longitude": f"longitude must be a float: {e}",
        }
    try:
        revision_acteur = RevisionActeur(**data_latlong_to_location(values_to_update))
        revision_acteur.full_clean()
    except ValidationError as e:
        logger.warning(f"RevisionActeur is not valid: {e}")
        return e.error_dict
    except TypeError as e:
        logger.warning(f"RevisionActeur is not valid: {e}")
        return {"error": str(e)}

    return {}


def serialize_suggestion_groupe(
    suggestion_groupe: SuggestionGroupe,
) -> SuggestionCohorteSerializer:
    """Serialize a SuggestionGroupe using SuggestionSourceType for validation"""
    # Get all suggestion_unitaires
    suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())

    # Get all suggestion_unitaires for Acteur
    acteur_suggestion_unitaires = {
        tuple(unit.champs): unit.valeurs
        for unit in suggestion_unitaires
        if unit.suggestion_modele == "Acteur"
    }
    acteur_overridden_by_suggestion_unitaires = {
        tuple(unit.champs): unit.valeurs
        for unit in suggestion_unitaires
        if unit.suggestion_modele == "RevisionActeur"
    }
    fields_groups = _get_ordered_fields_groups(
        acteur_suggestion_unitaires, acteur_overridden_by_suggestion_unitaires
    )
    acteur_overridden_by_suggestion_unitaires_by_field = _flatten_suggestion_unitaires(
        acteur_overridden_by_suggestion_unitaires
    )

    if (
        suggestion_groupe.suggestion_cohorte.type_action
        == SuggestionAction.SOURCE_AJOUT
    ):
        identifiant_unique = (
            suggestion_groupe.get_identifiant_unique_from_suggestion_unitaires()
        )
        fields_values = {
            key: {
                "displayed_value": value,
                "new_value": value,
                "updated_displayed_value": (
                    acteur_overridden_by_suggestion_unitaires_by_field.get(key, "")
                ),
            }
            for fields, values in acteur_suggestion_unitaires.items()
            for key, value in zip(fields, values)
        }
        return SuggestionCohorteSerializer(
            **_build_serializer_common_fields(suggestion_groupe),
            identifiant_unique=identifiant_unique,
            fields_groups=fields_groups,
            fields_values=fields_values,
        )

    acteur = suggestion_groupe.acteur
    acteur_overridden_by = suggestion_groupe.acteur_overridden_by()

    fields_groups = _get_ordered_fields_groups(acteur_suggestion_unitaires)

    fields = [key for keys in fields_groups for key in keys]

    acteur_suggestion_unitaires_by_field = _flatten_suggestion_unitaires(
        acteur_suggestion_unitaires
    )
    displayed_values = {}
    for field in fields:
        if field in SuggestionSourceType.get_not_editable_fields():
            continue
        value = getattr(acteur_overridden_by, field) if acteur_overridden_by else None
        if value is None:
            value = acteur_suggestion_unitaires_by_field.get(field)
            if value is None:
                value = getattr(acteur, field)
        displayed_values[field] = str(value)

    fields_values = {}
    for field in fields:
        fields_values[field] = {
            "displayed_value": str(displayed_values.get(field, "")),
            "updated_displayed_value": (
                str(acteur_overridden_by_suggestion_unitaires_by_field.get(field, ""))
            ),
            "new_value": str(acteur_suggestion_unitaires_by_field.get(field, "")),
            "old_value": str(getattr(acteur, field, "")),
        }

    return SuggestionCohorteSerializer(
        **_build_serializer_common_fields(suggestion_groupe),
        fields_groups=fields_groups,
        fields_values=fields_values,
        acteur=acteur,
        identifiant_unique=acteur.identifiant_unique,
        acteur_overridden_by=acteur_overridden_by,
    )


def update_suggestion_groupe(
    suggestion_groupe: SuggestionGroupe,
    fields_values: dict,
    fields_groups: list[tuple],
) -> tuple[bool, dict | None]:
    """
    Try to create the RevisionActeur Suggestions using SuggestionSourceType for
    validation
    Returns a tuple with:
    - bool: True if the update is successful, False otherwise
    - dict: None if the update is successful, a dictionary of errors otherwise
      general errors are under the key "error"
      field errors are under the key "field_name"
    """
    # Build mapping of existing revision suggestions by field
    revision_suggestion_unitaire_by_field = {
        field: value
        for unit in suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        )
        for field, value in zip(unit.champs, unit.valeurs)
    }

    # Determine which fields need to be updated using SuggestionSourceType
    values_to_update = {
        field: by_state_values["updated_displayed_value"]
        for field, by_state_values in fields_values.items()
        if field not in SuggestionSourceType.get_not_editable_fields()
        and "updated_displayed_value" in by_state_values
        and (
            by_state_values["updated_displayed_value"]
            != by_state_values["displayed_value"]
            or (
                field in revision_suggestion_unitaire_by_field
                and revision_suggestion_unitaire_by_field[field]
                != by_state_values["updated_displayed_value"]
            )
        )
    }
    values_to_update = {k: v for k, v in values_to_update.items() if v != ""}

    # Validate proposed updates
    if errors := _validate_proposed_updates(values_to_update, fields_values):
        return False, errors

    # Create or update SuggestionUnitaire objects
    for fields in fields_groups:
        if any(field in values_to_update for field in fields):
            suggestion_unitaire, _ = SuggestionUnitaire.objects.get_or_create(
                suggestion_groupe=suggestion_groupe,
                champs=fields,
                suggestion_modele="RevisionActeur",
                defaults={
                    "acteur": suggestion_groupe.acteur,
                    "revision_acteur": suggestion_groupe.revision_acteur,
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

    def _manage_tab_in_context(self, context, request, suggestion_groupe):
        def _append_location_to_points(
            points, latitude_data, longitude_data, key, color, draggable
        ):
            points.append(
                {
                    "latitude": float(latitude_data[key]),
                    "longitude": float(longitude_data[key]),
                    "color": color,
                    "key": key,
                    "draggable": draggable,
                }
            )

        context["tab"] = request.GET.get("tab", request.POST.get("tab", None))
        if context["tab"] == "acteur":
            context["uuid"] = suggestion_groupe.displayed_acteur_uuid
        if context["tab"] == "localisation":
            if (
                "latitude" in context["fields_values"]
                and "longitude" in context["fields_values"]
            ):
                latitude_data = context["fields_values"]["latitude"]
                longitude_data = context["fields_values"]["longitude"]

                # Prepare point list to display in map
                points = []

                # Point pour old_value (rouge, non draggable)
                if latitude_data.get("old_value") and longitude_data.get("old_value"):
                    points.append(
                        {
                            "latitude": float(latitude_data["old_value"]),
                            "longitude": float(longitude_data["old_value"]),
                            "color": "red",
                            "draggable": False,
                        }
                    )

                # Point pour new_value (vert #26A69A, non draggable)
                if latitude_data.get("new_value") and longitude_data.get("new_value"):
                    points.append(
                        {
                            "latitude": float(latitude_data["new_value"]),
                            "longitude": float(longitude_data["new_value"]),
                            "color": "blue",
                            "draggable": False,
                        }
                    )

                if latitude_data.get("updated_displayed_value") and longitude_data.get(
                    "updated_displayed_value"
                ):
                    points.append(
                        {
                            "latitude": float(latitude_data["updated_displayed_value"]),
                            "longitude": float(
                                longitude_data["updated_displayed_value"]
                            ),
                            "color": "green",
                            "draggable": True,
                        }
                    )
                elif latitude_data.get("displayed_value") and longitude_data.get(
                    "displayed_value"
                ):
                    _append_location_to_points(
                        points,
                        latitude_data,
                        longitude_data,
                        "displayed_value",
                        "#00695C",
                        True,
                    )
                context["localisation"] = {
                    "points": points,
                }

        return context

    def get(self, request, suggestion_groupe_id):
        suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)

        context = serialize_suggestion_groupe(suggestion_groupe).to_dict()
        context = self._manage_tab_in_context(context, request, suggestion_groupe)

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
            suggestion_groupe, fields_values, fields_groups
        )
        context = serialize_suggestion_groupe(suggestion_groupe).to_dict()
        context["errors"] = errors
        context = self._manage_tab_in_context(context, request, suggestion_groupe)

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )
