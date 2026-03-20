import json
import logging

from data.forms import SuggestionGroupeStatusForm
from data.models.suggestion import (
    SuggestionAction,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.models.suggestions.enrich_multi import SuggestionGroupeTypeEnrichMulti
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


def get_context_from_suggestion_groupe(
    suggestion_groupe: SuggestionGroupe,
) -> dict:
    """ """
    type_action = suggestion_groupe.suggestion_cohorte.type_action

    if type_action in [
        SuggestionAction.SOURCE_AJOUT,
        SuggestionAction.SOURCE_MODIFICATION,
        SuggestionAction.SOURCE_SUPPRESSION,
    ]:
        return get_context_from_suggestion_groupe_type_source(suggestion_groupe)
    elif type_action in [
        SuggestionAction.CRAWL_URLS,
    ]:
        return get_context_from_suggestion_groupe_type_enrich_multi(suggestion_groupe)

    raise NotImplementedError(f"Not implemented for type_action: {type_action}")


def get_context_from_suggestion_groupe_type_enrich_multi(
    suggestion_groupe: SuggestionGroupe,
) -> dict:
    """
    Serialize a SuggestionGroupe into a SuggestionGroupeTypeEnrichMulti and
    return a template context dict with the ComparisonTable.
    """
    sg_type_enrich_multi = SuggestionGroupeTypeEnrichMulti.from_suggestion_groupe(
        suggestion_groupe
    )
    context: dict = {
        "suggestion_groupe": suggestion_groupe,
        "suggestion_groupe_type": sg_type_enrich_multi,
        "comparison_table": sg_type_enrich_multi.to_comparison_table(),
    }
    return context


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
        - suggestion_groupe_type: the SuggestionGroupeTypeSource instance
        - acteur, revision_acteur, parent_revision_acteur (for non-SOURCE_AJOUT)
    """
    sg_type_source = SuggestionGroupeTypeSource.from_suggestion_groupe(
        suggestion_groupe
    )

    context: dict = {
        "suggestion_groupe": suggestion_groupe,
        "identifiant_unique": sg_type_source.identifiant_unique,
        "suggestion_groupe_type": sg_type_source,
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
    identifiant_unique: str = "",
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
                    return {coord_field: f"{coord_field} must be a float: {e}"}

        try:
            values_to_update = prepare_acteur_data_with_location(values_to_update)
        except (ValueError, KeyError) as e:
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
            return e.error_dict
        except TypeError as e:
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
    if not identifiant_unique:
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
        return False, {"error": str(e)}

    # Create or update SuggestionUnitaire objects
    for fields in fields_groups:
        if any(field in values_to_update for field in fields):
            suggestion_fields = {
                "suggestion_groupe": suggestion_groupe,
                "champs": fields,
                "suggestion_modele": suggestion_modele,
            }
            if suggestion_modele == "Acteur":
                suggestion_fields["acteur_id"] = identifiant_unique
            elif suggestion_modele == "RevisionActeur":
                suggestion_fields["revision_acteur_id"] = identifiant_unique
            elif suggestion_modele == "ParentRevisionActeur":
                suggestion_fields["parent_revision_acteur_id"] = identifiant_unique
            suggestion_unitaire, _ = SuggestionUnitaire.objects.get_or_create(
                **suggestion_fields
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

    @staticmethod
    def _find_latlong_suggestion(suggestion_unitaires, modele):
        return next(
            (
                su
                for su in suggestion_unitaires
                if su.suggestion_modele == modele
                and su.champs == ["latitude", "longitude"]
            ),
            None,
        )

    @staticmethod
    def _make_point(lat, lng, color, key, text=None, draggable=False):
        point = {
            "latitude": float(lat),
            "longitude": float(lng),
            "color": color,
            "key": key,
            "draggable": draggable,
        }
        if text is not None:
            point["text"] = text
        return point

    @staticmethod
    def _get_coords_from_suggestion_or_acteur(suggestion, acteur):
        if suggestion:
            return suggestion.valeurs[0], suggestion.valeurs[1]
        if acteur and acteur.latitude and acteur.longitude:
            return acteur.latitude, acteur.longitude
        return None, None

    def _manage_tab_in_context(
        self,
        *,
        tab: str | None,
        suggestion_groupe: SuggestionGroupe,
        acteur: Acteur | None,
        revision_acteur: RevisionActeur | None,
        parent_revision_acteur: RevisionActeur | None,
    ):
        context = {"tab": tab}
        if tab == "acteur":
            final_acteur = parent_revision_acteur or revision_acteur or acteur
            if final_acteur:
                displayed_acteur = DisplayedActeur.objects.filter(
                    identifiant_unique=final_acteur.identifiant_unique
                ).first()
                context["uuid"] = displayed_acteur.uuid if displayed_acteur else None

        if tab != "localisation":
            return context

        suggestion_unitaires = suggestion_groupe.suggestion_unitaires.all()
        points = []

        # Origin: acteur as saved in DB (not draggable)
        if acteur and acteur.latitude and acteur.longitude:
            points.append(
                self._make_point(acteur.latitude, acteur.longitude, "grey", "Origin")
            )

        # Suggestion: acteur as suggested by source (not draggable)
        acteur_suggestion = self._find_latlong_suggestion(
            suggestion_unitaires, "Acteur"
        )
        if acteur_suggestion:
            points.append(
                self._make_point(
                    acteur_suggestion.valeurs[0],
                    acteur_suggestion.valeurs[1],
                    "green",
                    "Suggestion",
                    text="A",
                )
            )

        # Correction: from suggestion if exists, else from revision_acteur (draggable)
        revision_suggestion = self._find_latlong_suggestion(
            suggestion_unitaires, "RevisionActeur"
        )
        lat, lng = self._get_coords_from_suggestion_or_acteur(
            revision_suggestion, revision_acteur
        )
        if lat is not None:
            points.append(
                self._make_point(
                    lat, lng, "blue", "RevisionActeur", text="▶️", draggable=True
                )
            )

        # Parent:
        # from suggestion if exists, else from parent_revision_acteur (draggable)
        parent_suggestion = self._find_latlong_suggestion(
            suggestion_unitaires, "ParentRevisionActeur"
        )
        lat, lng = self._get_coords_from_suggestion_or_acteur(
            parent_suggestion, parent_revision_acteur
        )
        if lat is not None:
            points.append(
                self._make_point(
                    lat, lng, "red", "ParentRevisionActeur", text="⏩", draggable=True
                )
            )

        if points:
            context["localisation"] = {"points": points}

        return context

    def _build_full_context(self, request, suggestion_groupe):
        if suggestion_groupe.suggestion_cohorte.type_action in [
            SuggestionAction.CRAWL_URLS,
        ]:
            return get_context_from_suggestion_groupe_type_enrich_multi(
                suggestion_groupe
            )
        else:
            context = get_context_from_suggestion_groupe_type_source(suggestion_groupe)
            tab_context = self._manage_tab_in_context(
                tab=request.GET.get("tab", request.POST.get("tab", None)),
                suggestion_groupe=suggestion_groupe,
                acteur=context.get("acteur"),
                revision_acteur=context.get("revision_acteur"),
                parent_revision_acteur=context.get("parent_revision_acteur"),
            )
            context.update(tab_context)
            return context

    def get(self, request, suggestion_groupe_id):
        suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)
        context = self._build_full_context(request, suggestion_groupe)
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
            suggestion_groupe,
            suggestion_modele_payload,
            fields_values,
            fields_groups,
            request.POST.get("identifiant_unique", ""),
        )

        context = self._build_full_context(request, suggestion_groupe)
        if errors:
            context["errors"] = errors
            suggestion_groupe_type = context["suggestion_groupe_type"]
            context["comparison_table"] = suggestion_groupe_type.to_comparison_table(
                errors=errors
            )

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )
