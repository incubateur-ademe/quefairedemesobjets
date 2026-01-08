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
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.models.suggestions.source import SuggestionSourceModel
from data.models.utils import prepare_acteur_data_with_location
from qfdmo.models.acteur import Acteur, ActeurStatus, RevisionActeur

logger = logging.getLogger(__name__)


def _build_serializer_common_fields(suggestion_groupe: SuggestionGroupe) -> dict:
    """Build common fields"""
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


def _dict_to_suggestion_source_model(
    values_dict: dict[str, str],
) -> SuggestionSourceModel:
    """
    Convert a dictionary of field values to a SuggestionSourceModel
    force None values to empty strings
    """

    return SuggestionSourceModel(
        **{key: values_dict.get(key, "") for key in values_dict.keys()}
    )


def _extract_acteur_values(
    acteur: Acteur | RevisionActeur, fields_to_include: list[str] | None = None
) -> SuggestionSourceModel:
    """
    Extract values from an Acteur or RevisionActeur instance
    using SuggestionSourceModel fields.
    Returns a SuggestionSourceModel instance with extracted values.
    Empty string is returned for missing or None values.
    """

    def get_field_from_code(acteur: Acteur | RevisionActeur, field_name: str) -> str:
        """Extract code from a ForeignKey field."""
        if field_name == "source_code":
            source_obj = getattr(acteur, "source", None)
            return source_obj.code if source_obj else ""
        if not field_name.endswith("_code"):
            raise ValueError(f"Field {field_name} is not a code field")
        fk_field_name = field_name.removesuffix("_code")
        object_field = getattr(acteur, fk_field_name, None)
        return object_field.code if object_field else ""

    def get_field_from_proposition_service_codes(
        acteur: Acteur | RevisionActeur,
    ) -> str:
        """Extract proposition_service_codes as JSON string."""
        prop_services = (
            list(acteur.proposition_services.all())
            if hasattr(acteur, "proposition_services")
            else []
        )
        if prop_services:
            prop_data = sorted(
                [
                    {
                        "action": prop.action.code,
                        "sous_categories": sorted(
                            [sc.code for sc in prop.sous_categories.all()]
                        ),
                    }
                    for prop in prop_services
                ],
                key=lambda x: x["action"],
            )
            return json.dumps(prop_data, ensure_ascii=False).replace('"', "'")
        return ""

    def get_field_from_perimetre_adomicile_codes(
        acteur: Acteur | RevisionActeur,
    ) -> str:
        """Extract perimetre_adomicile_codes as JSON string."""
        perimetres = (
            list(acteur.perimetre_adomiciles.all())
            if hasattr(acteur, "perimetre_adomiciles")
            else []
        )
        return (
            json.dumps(
                sorted(
                    [
                        {"type": perimetre.type, "valeur": perimetre.valeur}
                        for perimetre in perimetres
                    ],
                    key=lambda x: (x["type"], x["valeur"]),
                ),
                ensure_ascii=False,
            ).replace('"', "'")
            if perimetres
            else ""
        )

    def get_field_from_codes(acteur: Acteur | RevisionActeur, field_name: str) -> str:
        """Extract codes from ManyToMany fields as JSON string."""
        if not field_name.endswith("_codes"):
            raise ValueError(f"Field {field_name} is not a codes field")
        # Remove _codes suffix and add 's' to get the ManyToMany field name
        # e.g., label_codes -> labels, acteur_service_codes -> acteur_services
        m2m_field_name = field_name.removesuffix("_codes") + "s"
        m2m_objects = (
            list(getattr(acteur, m2m_field_name).all())
            if hasattr(acteur, m2m_field_name)
            else []
        )
        return (
            json.dumps(
                sorted([obj.code for obj in m2m_objects]), ensure_ascii=False
            ).replace('"', "'")
            if m2m_objects
            else ""
        )

    model_fields = SuggestionSourceModel.model_fields.keys()
    fields_to_process = fields_to_include if fields_to_include else list(model_fields)

    values = {}
    for field_name in fields_to_process:
        if field_name not in model_fields:
            raise ValueError(f"Field {field_name} not found in SuggestionSourceModel")
        if field_name.endswith("_code"):
            values[field_name] = get_field_from_code(acteur, field_name)
        elif field_name == "proposition_service_codes":
            values[field_name] = get_field_from_proposition_service_codes(acteur)
        elif field_name == "perimetre_adomicile_codes":
            values[field_name] = get_field_from_perimetre_adomicile_codes(acteur)
        elif field_name.endswith("_codes"):
            values[field_name] = get_field_from_codes(acteur, field_name)
        else:
            # Handle regular fields
            value = getattr(acteur, field_name, None)
            values[field_name] = str(value) if value is not None else ""

    return SuggestionSourceModel(**values)


def _get_ordered_fields_groups(
    suggestion_unitaires: list[SuggestionUnitaire],
) -> list[tuple]:
    """Get ordered fields groups using SuggestionSourceType validation"""

    all_suggestion_unitaires = {
        tuple(unit.champs): unit.valeurs for unit in suggestion_unitaires
    }

    fields_groups = list(set(all_suggestion_unitaires.keys()))

    # Validate using SuggestionSourceType
    ordered_fields = SuggestionSourceModel.get_ordered_fields()
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


def _suggestion_unitaires_to_suggestion_source_model_by_model_name(
    suggestion_unitaires: list[SuggestionUnitaire],
    model_name: str,
    revision_acteur_id: int | None = None,
) -> SuggestionSourceModel:
    suggestion_unitaires_dict = {
        tuple(unit.champs): unit.valeurs
        for unit in suggestion_unitaires
        if unit.suggestion_modele == model_name
        and (
            revision_acteur_id is None or unit.revision_acteur_id == revision_acteur_id
        )
    }
    return _dict_to_suggestion_source_model(
        _flatten_suggestion_unitaires(suggestion_unitaires_dict)
    )


def serialize_suggestion_groupe(
    suggestion_groupe: SuggestionGroupe,
) -> dict:
    """Serialize a SuggestionGroupe using SuggestionSourceModel for validation"""
    # Get all suggestion_unitaires
    suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())
    # Flatten and convert to SuggestionSourceModel
    acteur_suggestion_unitaires_by_field = (
        _suggestion_unitaires_to_suggestion_source_model_by_model_name(
            suggestion_unitaires, "Acteur"
        )
    )
    # Flatten and convert to SuggestionSourceModel
    acteur_overridden_by_suggestion_unitaires_by_field = (
        _suggestion_unitaires_to_suggestion_source_model_by_model_name(
            suggestion_unitaires,
            "RevisionActeur",
            revision_acteur_id=suggestion_groupe.revision_acteur_id,
        )
    )
    fields_groups = _get_ordered_fields_groups(suggestion_unitaires)
    flattened_fields_groups = [key for keys in fields_groups for key in keys]

    if (
        suggestion_groupe.suggestion_cohorte.type_action
        == SuggestionAction.SOURCE_AJOUT
    ):
        identifiant_unique = (
            suggestion_groupe.get_identifiant_unique_from_suggestion_unitaires("Acteur")
        )
        # Get fields from acteur_suggestion_unitaires
        fields_values = {
            key: {
                "displayed_value": getattr(
                    acteur_suggestion_unitaires_by_field, key, None
                ),
                "new_value": getattr(acteur_suggestion_unitaires_by_field, key, None),
                "updated_displayed_value": (
                    getattr(
                        acteur_overridden_by_suggestion_unitaires_by_field, key, None
                    )
                ),
            }
            for key in flattened_fields_groups
        }
        return {
            **_build_serializer_common_fields(suggestion_groupe),
            "identifiant_unique": identifiant_unique,
            "fields_groups": fields_groups,
            "fields_values": fields_values,
            "acteur": suggestion_groupe.acteur,
            "acteur_overridden_by": suggestion_groupe.revision_acteur,
        }

    acteur = suggestion_groupe.acteur
    acteur_overridden_by = suggestion_groupe.revision_acteur

    if not acteur:
        raise ValueError("acteur is required for non-SOURCE_AJOUT suggestions")

    # Extract values using SuggestionSourceModel
    acteur_values = _extract_acteur_values(
        acteur, fields_to_include=flattened_fields_groups
    )
    acteur_overridden_by_values = {}
    if acteur_overridden_by:
        acteur_overridden_by_values = _extract_acteur_values(
            acteur_overridden_by, fields_to_include=flattened_fields_groups
        )

    # Build displayed_values: priority is
    # acteur_overridden_by > acteur_suggestion_unitaires > acteur
    displayed_values_dict = {}
    for field in flattened_fields_groups:
        if field in SuggestionSourceModel.get_not_editable_fields():
            continue
        value = getattr(acteur_overridden_by_values, field, None)
        if value is None or value == "":
            value = getattr(acteur_suggestion_unitaires_by_field, field, None) or ""
        if value is None or value == "":
            value = getattr(acteur_values, field, "") or ""
        displayed_values_dict[field] = str(value) if value is not None else ""

    displayed_values = SuggestionSourceModel(**displayed_values_dict)

    fields_values = {}
    for field in flattened_fields_groups:
        fields_values[field] = {
            "displayed_value": getattr(displayed_values, field, None),
            "updated_displayed_value": (
                getattr(acteur_overridden_by_suggestion_unitaires_by_field, field, None)
            ),
            "new_value": getattr(acteur_suggestion_unitaires_by_field, field, None),
            "old_value": getattr(acteur_values, field, None),
        }

    return {
        **_build_serializer_common_fields(suggestion_groupe),
        "fields_groups": fields_groups,
        "fields_values": fields_values,
        "acteur": acteur,
        "identifiant_unique": acteur.identifiant_unique,
        "acteur_overridden_by": acteur_overridden_by,
    }


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
    suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())
    # Flatten and convert to SuggestionSourceModel
    revision_suggestion_unitaire_by_field = (
        _suggestion_unitaires_to_suggestion_source_model_by_model_name(
            suggestion_unitaires, "RevisionActeur"
        )
    )

    # Determine which fields need to be updated using SuggestionSourceType
    values_to_update = {
        field: by_state_values["updated_displayed_value"]
        for field, by_state_values in fields_values.items()
        if field not in SuggestionSourceModel.get_not_editable_fields()
        and "updated_displayed_value" in by_state_values
        and (
            by_state_values["updated_displayed_value"]
            != by_state_values["displayed_value"]
            or (
                getattr(revision_suggestion_unitaire_by_field, field, None) is not None
                and getattr(revision_suggestion_unitaire_by_field, field, None)
                != by_state_values["updated_displayed_value"]
            )
        )
    }

    if suggestion_groupe.revision_acteur is None:
        suggestion_groupe.revision_acteur = (
            suggestion_groupe.acteur.get_or_create_revision()
        )
        suggestion_groupe.save()

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
                suggestion_modele="RevisionActeur",
                defaults={
                    "acteur": suggestion_groupe.acteur,
                    "revision_acteur_id": suggestion_groupe.revision_acteur,
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

        context = serialize_suggestion_groupe(suggestion_groupe)
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
        context = serialize_suggestion_groupe(suggestion_groupe)
        context["errors"] = errors
        context = self._manage_tab_in_context(context, request, suggestion_groupe)

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )
