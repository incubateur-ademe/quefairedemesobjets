import json
import logging

from core.templatetags.admin_data_tags import display_diff_values
from data.forms import SuggestionGroupeStatusForm
from data.models.comparison_table import (
    CellContent,
    CellField,
    ColumnHeader,
    ComparisonTable,
    HeaderLink,
    StimulusControllerConfig,
    TableRow,
)
from data.models.suggestion import (
    SuggestionAction,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.models.suggestions.source import SuggestionSourceModel
from data.models.utils import prepare_acteur_data_with_location
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import FormView, View
from more_itertools import flatten
from qfdmo.models.acteur import Acteur, ActeurStatus, DisplayedActeur, RevisionActeur

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
            return json.dumps(prop_data, ensure_ascii=False)
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
            )
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
            json.dumps(sorted([obj.code for obj in m2m_objects]), ensure_ascii=False)
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


def _suggestion_unitaires_to_suggestion_source_model_by_model_name(
    suggestion_unitaires: list[SuggestionUnitaire],
    model_name: str,
) -> SuggestionSourceModel:
    suggestion_unitaires_dict = {
        tuple(unit.champs): unit.valeurs
        for unit in suggestion_unitaires
        if unit.suggestion_modele == model_name
    }
    return _dict_to_suggestion_source_model(
        _flatten_suggestion_unitaires(suggestion_unitaires_dict)
    )


def _field_without_suggestion_display(field_value: str | None) -> str:
    if field_value is None or field_value == "":
        field_value = "-"
    return mark_safe(f'<span class="no-suggestion-text">{field_value}</span>')


def _display_suggestion_unitaire_for_a_field(
    field_name: str,
    suggestion_source_model: SuggestionSourceModel,
    field_value: str | None = None,
) -> str:
    suggestion_unitaire = getattr(suggestion_source_model, field_name)
    if suggestion_unitaire is None:
        return _field_without_suggestion_display(field_value)
    return display_diff_values(field_value, suggestion_unitaire)


def _build_comparison_table_for_type_source(
    fields_groups: list[tuple],
    update_url: str = "",
    acteur: Acteur | None = None,
    revision_acteur: RevisionActeur | None = None,
    parent_revision_acteur: RevisionActeur | None = None,
    acteur_suggestion_unitaires_by_field: (
        SuggestionSourceModel
    ) = SuggestionSourceModel(),
    revision_acteur_suggestion_unitaires_by_field: (
        SuggestionSourceModel
    ) = SuggestionSourceModel(),
    parent_revision_acteur_suggestion_unitaires_by_field: (
        SuggestionSourceModel
    ) = SuggestionSourceModel(),
    errors: dict | None = None,
) -> ComparisonTable:
    """Build a domain-agnostic ComparisonTable from suggestion data."""
    not_editable = SuggestionSourceModel.get_not_editable_fields()
    not_reportable_revision = (
        SuggestionSourceModel.get_not_reportable_on_revision_fields()
    )
    not_reportable_parent = SuggestionSourceModel.get_not_reportable_on_parent_fields()
    fields_groups_json = json.dumps(fields_groups)
    flattened = [key for keys in fields_groups for key in keys]

    acteur_values = (
        _extract_acteur_values(acteur, fields_to_include=flattened)
        if acteur
        else SuggestionSourceModel()
    )

    revision_acteur_values = (
        _extract_acteur_values(revision_acteur, fields_to_include=flattened)
        if revision_acteur
        else SuggestionSourceModel()
    )

    parent_revision_acteur_values = (
        _extract_acteur_values(parent_revision_acteur, fields_to_include=flattened)
        if parent_revision_acteur
        else SuggestionSourceModel()
    )

    def _get_field_value(model, field):
        return getattr(model, field, None) if model else None

    def _target_values_json(fields):
        return json.dumps(
            {
                field: getattr(acteur_suggestion_unitaires_by_field, field)
                for field in fields
                if getattr(acteur_suggestion_unitaires_by_field, field, None)
                is not None
            }
        )

    def _revision_replace_text(field):
        return (
            getattr(
                revision_acteur_suggestion_unitaires_by_field,
                field,
                None,
            )
            or getattr(
                acteur_suggestion_unitaires_by_field,
                field,
                None,
            )
            or ""
        )

    def _parent_replace_text(field):
        return (
            getattr(
                parent_revision_acteur_suggestion_unitaires_by_field,
                field,
                None,
            )
            or getattr(
                acteur_suggestion_unitaires_by_field,
                field,
                None,
            )
            or ""
        )

    def _source_display(field):
        return _display_suggestion_unitaire_for_a_field(
            field,
            acteur_suggestion_unitaires_by_field,
            _get_field_value(acteur_values, field),
        )

    def _revision_display(field):
        return _display_suggestion_unitaire_for_a_field(
            field,
            revision_acteur_suggestion_unitaires_by_field,
            _get_field_value(revision_acteur_values, field),
        )

    def _parent_display(field):
        return _display_suggestion_unitaire_for_a_field(
            field,
            parent_revision_acteur_suggestion_unitaires_by_field,
            _get_field_value(parent_revision_acteur_values, field),
        )

    # --- Columns ---
    columns = [
        ColumnHeader(key="label", css_classes="qf-w-1/4"),
        ColumnHeader(
            key="source",
            label="Acteur Importé",
            css_classes="qf-w-1/4",
            links=(
                [HeaderLink(label="importé", url=acteur.change_url)] if acteur else []
            ),
        ),
        ColumnHeader(
            key="report_revision",
            label="▶️",
            css_classes="qf-text-center qf-text-2xl",
            header_action=StimulusControllerConfig(
                controller="report-update",
                values={
                    "fields": "|".join(flattened),
                    "suggestion-modele": "RevisionActeur",
                    "update-url": update_url,
                    "target-values": _target_values_json(flattened),
                    "fields-groups": fields_groups_json,
                },
                actions=["click->report-update#report"],
            ),
        ),
    ]

    # Correction column
    correction_links = []
    if revision_acteur:
        correction_links.append(
            HeaderLink(label="corrigé", url=revision_acteur.change_url)
        )
        if not parent_revision_acteur:
            correction_links.append(
                HeaderLink(
                    label="affiché",
                    url=revision_acteur.displayedacteur_change_url,
                )
            )
    columns.append(
        ColumnHeader(
            key="correction",
            label="Correction",
            css_classes="qf-w-1/4",
            links=correction_links,
        )
    )

    # Parent columns (conditional)
    if parent_revision_acteur:
        columns.append(
            ColumnHeader(
                key="report_parent",
                label="⏩",
                css_classes="qf-text-center qf-text-2xl",
                header_action=StimulusControllerConfig(
                    controller="report-update",
                    values={
                        "fields": "|".join(flattened),
                        "suggestion-modele": "ParentRevisionActeur",
                        "update-url": update_url,
                        "target-values": _target_values_json(flattened),
                        "fields-groups": fields_groups_json,
                    },
                    actions=["click->report-update#report"],
                ),
            )
        )
        parent_links = [
            HeaderLink(label="corrigé", url=parent_revision_acteur.change_url),
            HeaderLink(
                label="affiché",
                url=parent_revision_acteur.displayedacteur_change_url,
            ),
        ]
        columns.append(
            ColumnHeader(
                key="parent",
                label="Parent",
                css_classes="qf-w-1/4",
                links=parent_links,
                subtitle=(
                    f"{parent_revision_acteur.nombre_enfants} enfants impactés"
                    if parent_revision_acteur.nombre_enfants
                    else None
                ),
            )
        )

    # --- Rows ---
    rows = []
    for field_group in fields_groups:
        fields_str = "|".join(field_group)
        cells: list[CellContent] = []

        # Source (display) cell
        cells.append(
            CellContent(
                column_key="source",
                cell_type="display",
                fields=[
                    CellField(
                        field_name=field,
                        display_html=_source_display(field),
                    )
                    for field in field_group
                ],
            )
        )

        # Report to revision (action) cell
        reportable_on_revision = all(
            f not in not_reportable_revision for f in field_group
        )
        cells.append(
            CellContent(
                column_key="report_revision",
                cell_type="action",
                enabled=reportable_on_revision,
                action_icon="▶️",
                stimulus=(
                    StimulusControllerConfig(
                        controller="report-update",
                        values={
                            "fields": fields_str,
                            "suggestion-modele": "RevisionActeur",
                            "update-url": update_url,
                            "target-values": _target_values_json(field_group),
                            "fields-groups": fields_groups_json,
                        },
                        actions=["click->report-update#report"],
                    )
                    if reportable_on_revision
                    else None
                ),
            )
        )

        # Correction (editable) cell
        cells.append(
            CellContent(
                column_key="correction",
                cell_type="editable",
                fields=[
                    CellField(
                        field_name=field,
                        display_html=_revision_display(field),
                        editable=field not in not_editable,
                        stimulus=(
                            StimulusControllerConfig(
                                controller="cell-edit",
                                values={
                                    "field": field,
                                    "suggestion-modele": "RevisionActeur",
                                    "update-url": update_url,
                                    "replace-text": _revision_replace_text(field),
                                    "fields-groups": fields_groups_json,
                                },
                                actions=[
                                    "blur->cell-edit#save",
                                    "focus->cell-edit#replace",
                                ],
                            )
                            if field not in not_editable
                            else None
                        ),
                        error=(
                            str(errors.get(field, ""))
                            if errors and errors.get(field)
                            else None
                        ),
                    )
                    for field in field_group
                ],
            )
        )

        # Parent columns (conditional)
        if parent_revision_acteur:
            reportable_on_parent = all(
                f not in not_reportable_parent for f in field_group
            )
            cells.append(
                CellContent(
                    column_key="report_parent",
                    cell_type="action",
                    enabled=reportable_on_parent,
                    action_icon="⏩",
                    stimulus=(
                        StimulusControllerConfig(
                            controller="report-update",
                            values={
                                "fields": fields_str,
                                "suggestion-modele": "ParentRevisionActeur",
                                "update-url": update_url,
                                "target-values": _target_values_json(field_group),
                                "fields-groups": fields_groups_json,
                            },
                            actions=["click->report-update#report"],
                        )
                        if reportable_on_parent
                        else None
                    ),
                )
            )

            cells.append(
                CellContent(
                    column_key="parent",
                    cell_type="editable",
                    fields=[
                        CellField(
                            field_name=field,
                            display_html=_parent_display(field),
                            editable=field not in not_editable,
                            stimulus=(
                                StimulusControllerConfig(
                                    controller="cell-edit",
                                    values={
                                        "field": field,
                                        "suggestion-modele": "ParentRevisionActeur",
                                        "update-url": update_url,
                                        "replace-text": _parent_replace_text(field),
                                        "fields-groups": fields_groups_json,
                                    },
                                    actions=[
                                        "blur->cell-edit#save",
                                        "focus->cell-edit#replace",
                                    ],
                                )
                                if field not in not_editable
                                else None
                            ),
                            error=(
                                str(errors.get(field, ""))
                                if errors and errors.get(field)
                                else None
                            ),
                        )
                        for field in field_group
                    ],
                )
            )

        rows.append(TableRow(label=", ".join(field_group), cells=cells))

    return ComparisonTable(columns=columns, rows=rows)


def serialize_suggestion_groupe(
    suggestion_groupe: SuggestionGroupe,
) -> dict:
    """
    Serialize a SuggestionGroupe into a ComparisonTable for generic rendering.

    Collects suggestion_unitaires, groups them by field, and builds a
    ComparisonTable with one column per model (Acteur, RevisionActeur,
    ParentRevisionActeur) and one row per field_group.

    Each cell includes:
    - display_html: diff between current value and suggested value,
      or greyed-out current value when no suggestion exists
    - Stimulus controller configs (cell-edit, report-update) with
      pre-computed values (updateUrl, fieldsGroups, targetValues, replaceText)

    Returns a dict with:
        - suggestion_groupe: the SuggestionGroupe instance
        - identifiant_unique: the acteur identifier
        - comparison_table: a ComparisonTable Pydantic model
        - acteur, revision_acteur, parent_revision_acteur (for non-SOURCE_AJOUT)
    """
    # Get all suggestion_unitaires
    suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())
    # Flatten and convert to SuggestionSourceModel
    acteur_suggestion_unitaires_by_field = (
        _suggestion_unitaires_to_suggestion_source_model_by_model_name(
            suggestion_unitaires, "Acteur"
        )
    )
    # Flatten and convert to SuggestionSourceModel
    revision_acteur_suggestion_unitaires_by_field = (
        _suggestion_unitaires_to_suggestion_source_model_by_model_name(
            suggestion_unitaires,
            "RevisionActeur",
        )
    )
    fields_groups = _get_ordered_fields_groups(suggestion_unitaires)

    if (
        suggestion_groupe.suggestion_cohorte.type_action
        == SuggestionAction.SOURCE_AJOUT
    ):
        identifiant_unique = (
            suggestion_groupe.get_identifiant_unique_from_suggestion_unitaires("Acteur")
        )
        return {
            "suggestion_groupe": suggestion_groupe,
            "identifiant_unique": identifiant_unique,
            # TODO: simplifier la gestion des fields_groups et fields_values
            "comparison_table": _build_comparison_table_for_type_source(
                fields_groups=fields_groups,
                update_url=reverse(
                    "data:suggestion_groupe",
                    args=[suggestion_groupe.id],
                ),
                acteur_suggestion_unitaires_by_field=(
                    acteur_suggestion_unitaires_by_field
                ),
                revision_acteur_suggestion_unitaires_by_field=(
                    revision_acteur_suggestion_unitaires_by_field
                ),
            ),
        }

    acteur = suggestion_groupe.get_acteur_or_none()
    revision_acteur = suggestion_groupe.get_revision_acteur_or_none()
    parent_revision_acteur = suggestion_groupe.get_parent_revision_acteur_or_none()

    # Flatten and convert to SuggestionSourceModel
    parent_revision_acteur_suggestion_unitaires_by_field = (
        _suggestion_unitaires_to_suggestion_source_model_by_model_name(
            suggestion_unitaires,
            "ParentRevisionActeur",
        )
    )

    if not acteur:
        raise ValueError("acteur is required for non-SOURCE_AJOUT suggestions")

    return {
        "suggestion_groupe": suggestion_groupe,
        "identifiant_unique": acteur.identifiant_unique,
        "acteur": acteur,
        "revision_acteur": revision_acteur,
        "parent_revision_acteur": parent_revision_acteur,
        "comparison_table": _build_comparison_table_for_type_source(
            fields_groups=fields_groups,
            update_url=reverse(
                "data:suggestion_groupe",
                args=[suggestion_groupe.id],
            ),
            acteur=acteur,
            revision_acteur=revision_acteur,
            parent_revision_acteur=parent_revision_acteur,
            acteur_suggestion_unitaires_by_field=acteur_suggestion_unitaires_by_field,
            revision_acteur_suggestion_unitaires_by_field=(
                revision_acteur_suggestion_unitaires_by_field
            ),
            parent_revision_acteur_suggestion_unitaires_by_field=(
                parent_revision_acteur_suggestion_unitaires_by_field
            ),
        ),
    }


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
        _suggestion_unitaires_to_suggestion_source_model_by_model_name(
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

        context = serialize_suggestion_groupe(suggestion_groupe)
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

        context = serialize_suggestion_groupe(suggestion_groupe)
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
            context["comparison_table"] = _build_comparison_table_for_type_source(
                fields_groups=context["fields_groups"],
                update_url=reverse(
                    "data:suggestion_groupe",
                    args=[suggestion_groupe.id],
                ),
                acteur=context.get("acteur"),
                revision_acteur=context.get("revision_acteur"),
                parent_revision_acteur=context.get("parent_revision_acteur"),
                acteur_values=context.get("acteur_values"),
                revision_acteur_values=context.get("revision_acteur_values"),
                parent_revision_acteur_values=context.get(
                    "parent_revision_acteur_values"
                ),
                acteur_suggestion_unitaires_by_field=context.get(
                    "acteur_suggestion_unitaires_by_field"
                ),
                revision_acteur_suggestion_unitaires_by_field=context.get(
                    "revision_acteur_suggestion_unitaires_by_field"
                ),
                parent_revision_acteur_suggestion_unitaires_by_field=context.get(
                    "parent_revision_acteur_suggestion_unitaires_by_field"
                ),
                errors=errors,
            )

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )
