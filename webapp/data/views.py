import json
import logging
from collections import Counter

from core.views import IsStaffMixin
from data.forms import SuggestionGroupeStatusForm
from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
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
from django.db import transaction
from django.db.models import CharField, Exists, OuterRef, Q
from django.db.models.functions import Cast
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View
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
        "fields_groups": sg_type_source.fields_groups,
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
                    logger.warning(f"ValueError for {coord_field}: {e}")
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
        logger.warning(f"Error validating proposed updates: {e}")
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

        with transaction.atomic():
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
                context["comparison_table"] = (
                    suggestion_groupe_type.to_comparison_table(errors=errors)
                )

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )


REVIEW_ROWS_DEFAULT_LIMIT = 100
REVIEW_ROWS_MAX_LIMIT = 200
REVIEW_BULK_MAX_GROUPES = 1000


def build_pivot_row(groupe: SuggestionGroupe) -> dict:
    """Pivot row for the review grid, with a fallback for groupes the grid
    cannot represent (non-source cohortes, inconsistent data)."""
    try:
        return SuggestionGroupeTypeSource.from_suggestion_groupe(groupe).to_pivot_row()
    except ValueError as e:
        logger.warning(f"Cannot build pivot row for groupe {groupe.id}: {e}")
        return {
            "groupe_id": groupe.id,
            "statut": groupe.statut,
            "statut_display": groupe.get_statut_display(),
            "acteur_id": groupe.acteur_id or "",
            "acteur_nom": "",
            "has_parent": groupe.parent_revision_acteur_id is not None,
            "detail_url": groupe.admin_change_url,
            "cells": {},
            "error": "type de suggestion non supporté par la grille",
        }


def cohorte_fields_meta(cohorte: SuggestionCohorte) -> list[dict]:
    """One entry per field having at least one suggestion to validate in the
    cohorte, ordered like the detail view, with pending counts."""
    champs_lists = SuggestionUnitaire.objects.filter(
        suggestion_groupe__suggestion_cohorte=cohorte,
        suggestion_groupe__statut=SuggestionStatut.AVALIDER,
        suggestion_modele="Acteur",
        statut=SuggestionStatut.AVALIDER,
    ).values_list("champs", flat=True)

    pending: Counter = Counter()
    for champs in champs_lists:
        pending.update(champs)

    ordered = [
        field for group in SuggestionSourceModel.get_ordered_fields() for field in group
    ]
    keys = [field for field in ordered if field in pending]
    keys += sorted(field for field in pending if field not in ordered)
    return [{"key": key, "pending": pending[key]} for key in keys]


class CohorteReviewView(IsStaffMixin, TemplateView):
    """Pivot review screen for a cohorte: rows = suggestion groupes (acteurs),
    columns = fields. The grid itself is rendered client-side by the
    cohorte-review Stimulus controller, fed by CohorteReviewRowsView."""

    template_name = "data/cohorte_review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suggestion_cohorte"] = get_object_or_404(
            SuggestionCohorte, id=self.kwargs["cohorte_id"]
        )
        return context


# Query builder of the focus mode: lookups allowed on the suggested value.
# Keys are the client-side identifiers, values the ORM lookup applied to the
# first (and only) element of SuggestionUnitaire.valeurs.
REVIEW_VALUE_LOOKUPS = {
    "startswith": "istartswith",
    "endswith": "iendswith",
    "contains": "icontains",
    "exact": "iexact",
    "regex": "iregex",
}
REVIEW_VALUE_MAX_CONDITIONS = 10


def build_value_filter_q(valeur_filtre: dict) -> Q:
    """Translate the focus-mode query builder payload into a Q over
    SuggestionUnitaire rows.

    Expected shape: {"combinator": "et" | "ou", "conditions":
    [{"lookup": <REVIEW_VALUE_LOOKUPS key | empty | not_empty |
    not_contains>, "value": str}]}. Raises ValueError on anything else.
    """
    if not isinstance(valeur_filtre, dict):
        raise ValueError("valeur_filtre must be an object")
    combinator = valeur_filtre.get("combinator", "et")
    if combinator not in {"et", "ou"}:
        raise ValueError("combinator must be 'et' or 'ou'")
    conditions = valeur_filtre.get("conditions")
    if (
        not isinstance(conditions, list)
        or not conditions
        or len(conditions) > REVIEW_VALUE_MAX_CONDITIONS
    ):
        raise ValueError(
            "conditions must be a non-empty list of at most "
            f"{REVIEW_VALUE_MAX_CONDITIONS} items"
        )

    empty_q = Q(valeurs__0="") | Q(valeurs=[])
    condition_qs = []
    for condition in conditions:
        if not isinstance(condition, dict):
            raise ValueError("each condition must be an object")
        lookup = condition.get("lookup")
        value = str(condition.get("value", ""))
        if lookup == "empty":
            condition_qs.append(empty_q)
        elif lookup == "not_empty":
            condition_qs.append(~empty_q)
        elif lookup == "not_contains":
            if not value:
                raise ValueError(f"value is required for lookup '{lookup}'")
            condition_qs.append(~Q(valeurs__0__icontains=value))
        elif lookup in REVIEW_VALUE_LOOKUPS:
            if not value:
                raise ValueError(f"value is required for lookup '{lookup}'")
            condition_qs.append(
                Q(**{f"valeurs__0__{REVIEW_VALUE_LOOKUPS[lookup]}": value})
            )
        else:
            raise ValueError(f"unknown lookup '{lookup}'")

    combined = condition_qs[0]
    for condition_q in condition_qs[1:]:
        if combinator == "ou":
            combined = combined | condition_q
        else:
            combined = combined & condition_q
    return combined


def filter_review_groupes(
    cohorte: SuggestionCohorte,
    *,
    statut: str,
    champ: str | None,
    q: str,
    valeur_filtre: dict | None = None,
):
    """Shared filtering for the review grid: used by the rows endpoint and
    by the bulk endpoint's « all filtered rows » scope, so both always agree
    on what « filtered » means. Raises ValueError on an invalid
    valeur_filtre payload."""
    queryset = SuggestionGroupe.objects.filter(suggestion_cohorte=cohorte)
    if statut != "all":
        queryset = queryset.filter(statut=statut)
    if champ:
        queryset = queryset.filter(
            suggestion_unitaires__champs__contains=[champ]
        ).distinct()
    if q:
        # acteur is a FK with db_constraint=False: search the raw column
        # text rather than joining on a possibly missing Acteur row
        queryset = queryset.annotate(
            acteur_id_text=Cast("acteur_id", CharField())
        ).filter(acteur_id_text__icontains=q)
    if valeur_filtre is not None:
        if not champ:
            raise ValueError("valeur_filtre requires champ")
        # champs=[champ] (exact single-field match) guarantees valeurs[0] is
        # the value of that field — grouped fields (latitude/longitude) are
        # out of scope for the value query builder
        queryset = queryset.filter(
            Exists(
                SuggestionUnitaire.objects.filter(
                    suggestion_groupe=OuterRef("pk"),
                    suggestion_modele="Acteur",
                    champs=[champ],
                ).filter(build_value_filter_q(valeur_filtre))
            )
        )
    return queryset


class CohorteReviewRowsView(IsStaffMixin, View):
    """JSON rows endpoint for the cohorte review grid.

    Keyset pagination: stable ordering by id, `after` cursor, `limit` batch
    size. Filtering (statut, champ, q) stays server-side: the client only
    ever holds the rows it has fetched.
    """

    def get(self, request, cohorte_id):
        cohorte = get_object_or_404(SuggestionCohorte, id=cohorte_id)

        valeur_filtre = None
        if valeur_filtre_raw := request.GET.get("valeur_filtre"):
            try:
                valeur_filtre = json.loads(valeur_filtre_raw)
            except json.JSONDecodeError:
                return HttpResponseBadRequest("valeur_filtre must be valid JSON")

        try:
            queryset = filter_review_groupes(
                cohorte,
                statut=request.GET.get("statut", SuggestionStatut.AVALIDER),
                champ=request.GET.get("champ"),
                q=request.GET.get("q", ""),
                valeur_filtre=valeur_filtre,
            ).prefetch_related("suggestion_unitaires", "acteur", "revision_acteur")
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        total = queryset.count()

        try:
            after = int(request.GET.get("after", 0))
            limit = int(request.GET.get("limit", REVIEW_ROWS_DEFAULT_LIMIT))
        except ValueError:
            return HttpResponseBadRequest("after and limit must be integers")
        limit = max(1, min(limit, REVIEW_ROWS_MAX_LIMIT))

        groupes = list(queryset.filter(id__gt=after).order_by("id")[:limit])

        rows = [build_pivot_row(groupe) for groupe in groupes]
        next_after = groupes[-1].id if len(groupes) == limit else None

        return JsonResponse(
            {
                "rows": rows,
                "meta": {
                    "total": total,
                    "next_after": next_after,
                    "fields": cohorte_fields_meta(cohorte),
                },
            }
        )


REVIEW_BULK_ACTION_TO_STATUT = {
    "accept": SuggestionStatut.ATRAITER,
    "reject": SuggestionStatut.REJETEE,
    "reset": SuggestionStatut.AVALIDER,
}


class CohorteReviewBulkView(IsStaffMixin, View):
    """Per-field accept/reject on an explicit selection or on every
    filtered groupe.

    POST body (JSON): {champ: str | null, action: "accept" | "reject" |
    "reset"} plus exactly one scope:
    - groupe_ids: [int] — explicit selection; the refreshed pivot rows are
      returned so the grid updates in place;
    - filter: {statut, champ, q} — every groupe matching the same filters
      as the rows endpoint (Gmail-style « select all »); no rows are
      returned (the set may be huge), the client reloads.

    A null champ targets every field of the targeted groupes.
    """

    def post(self, request, cohorte_id):
        cohorte = get_object_or_404(SuggestionCohorte, id=cohorte_id)

        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("invalid JSON body")

        action = payload.get("action")
        if action not in REVIEW_BULK_ACTION_TO_STATUT:
            return HttpResponseBadRequest(
                "action must be one of: accept, reject, reset"
            )
        champ = payload.get("champ") or None

        groupe_ids = payload.get("groupe_ids")
        filter_payload = payload.get("filter")
        if (groupe_ids is None) == (filter_payload is None):
            return HttpResponseBadRequest("provide exactly one of groupe_ids or filter")

        if groupe_ids is not None:
            if (
                not isinstance(groupe_ids, list)
                or not groupe_ids
                or not all(isinstance(groupe_id, int) for groupe_id in groupe_ids)
            ):
                return HttpResponseBadRequest("groupe_ids must be a list of ids")
            if len(groupe_ids) > REVIEW_BULK_MAX_GROUPES:
                return HttpResponseBadRequest(
                    f"groupe_ids is limited to {REVIEW_BULK_MAX_GROUPES} entries"
                )
            # Scoping to the cohorte prevents acting on another cohorte's
            # groupes through forged ids.
            targeted = SuggestionGroupe.objects.filter(
                suggestion_cohorte=cohorte, id__in=groupe_ids
            )
        else:
            if not isinstance(filter_payload, dict):
                return HttpResponseBadRequest("filter must be an object")
            try:
                targeted = filter_review_groupes(
                    cohorte,
                    statut=filter_payload.get("statut") or SuggestionStatut.AVALIDER,
                    champ=filter_payload.get("champ") or None,
                    q=filter_payload.get("q") or "",
                    valeur_filtre=filter_payload.get("valeur_filtre"),
                )
            except ValueError as e:
                return HttpResponseBadRequest(str(e))

        with transaction.atomic():
            targeted_ids = list(targeted.values_list("id", flat=True))
            unitaires = SuggestionUnitaire.objects.filter(
                suggestion_groupe_id__in=targeted_ids,
                suggestion_modele="Acteur",
            )
            if champ:
                unitaires = unitaires.filter(champs__contains=[champ])
            applied = unitaires.update(statut=REVIEW_BULK_ACTION_TO_STATUT[action])

            self._derive_groupes_statut(targeted_ids)

        response: dict = {
            "applied": applied,
            "meta": {"fields": cohorte_fields_meta(cohorte)},
        }
        if groupe_ids is not None:
            response["rows"] = [
                build_pivot_row(groupe)
                for groupe in SuggestionGroupe.objects.filter(
                    id__in=targeted_ids
                ).prefetch_related("suggestion_unitaires", "acteur", "revision_acteur")
            ]
        return JsonResponse(response)

    @staticmethod
    def _derive_groupes_statut(groupe_ids: list[int]) -> None:
        """A groupe stays « à valider » while any of its source suggestions
        is undecided; once all are decided it becomes « à traiter » unless
        everything was rejected. Set-based so « select all filtered » stays
        fast on large cohortes."""

        def acteur_unitaires():
            return SuggestionUnitaire.objects.filter(
                suggestion_groupe=OuterRef("pk"), suggestion_modele="Acteur"
            )

        groupes = SuggestionGroupe.objects.filter(id__in=groupe_ids).annotate(
            has_source_suggestion=Exists(acteur_unitaires()),
            has_pending=Exists(
                acteur_unitaires().filter(statut=SuggestionStatut.AVALIDER)
            ),
            has_non_rejected_decision=Exists(
                acteur_unitaires().exclude(
                    statut__in=[
                        SuggestionStatut.AVALIDER,
                        SuggestionStatut.REJETEE,
                    ]
                )
            ),
        )
        groupes.filter(has_source_suggestion=True, has_pending=True).update(
            statut=SuggestionStatut.AVALIDER
        )
        groupes.filter(
            has_source_suggestion=True,
            has_pending=False,
            has_non_rejected_decision=True,
        ).update(statut=SuggestionStatut.ATRAITER)
        groupes.filter(
            has_source_suggestion=True,
            has_pending=False,
            has_non_rejected_decision=False,
        ).update(statut=SuggestionStatut.REJETEE)
