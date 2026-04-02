import json

from core.templatetags.admin_data_tags import display_diff_values
from data.models.comparison_table import (
    CellContent,
    CellField,
    CellFieldsContent,
    ColumnHeader,
    ComparisonTable,
    HeaderLink,
    StimulusControllerConfig,
    TableRow,
)
from data.models.suggestion import (
    SuggestionAction,
    SuggestionGroupe,
    SuggestionUnitaire,
)
from data.models.suggestions.abstract import SuggestionGroupeType
from django.urls import reverse
from django.utils.safestring import mark_safe
from more_itertools import flatten
from pydantic import BaseModel, ConfigDict
from qfdmo.models.acteur import Acteur, RevisionActeur


class SuggestionSourceModel(BaseModel):
    """
    This model is used to validate and manipulate the suggestion of source type.
    Represent any updates for a given object :
    Acteur, RevisionActeur, ParentRevisionActeur.
    """

    model_config = ConfigDict(frozen=True)

    # Définition de tous les champs comme attributs optionnels
    identifiant_unique: str | None = None
    source_code: str | None = None
    identifiant_externe: str | None = None
    nom: str | None = None
    nom_commercial: str | None = None
    nom_officiel: str | None = None
    siret: str | None = None
    siren: str | None = None
    naf_principal: str | None = None
    description: str | None = None
    acteur_type_code: str | None = None
    url: str | None = None
    email: str | None = None
    telephone: str | None = None
    adresse: str | None = None
    adresse_complement: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    horaires_osm: str | None = None
    horaires_description: str | None = None
    public_accueilli: str | None = None
    reprise: str | None = None
    exclusivite_de_reprisereparation: str | None = None
    uniquement_sur_rdv: str | None = None
    consignes_dacces: str | None = None
    statut: str | None = None
    commentaires: str | None = None
    label_codes: str | None = None
    acteur_service_codes: str | None = None
    proposition_service_codes: str | None = None
    lieu_prestation: str | None = None
    perimetre_adomicile_codes: str | None = None

    @classmethod
    def from_json(cls, json_data: str) -> "SuggestionSourceModel":
        data = json.loads(json_data)
        for key, value in data.items():
            if key.endswith("_codes"):
                data[key] = json.dumps(value)
            elif value is not None and value != "":
                data[key] = str(value)
        return cls.model_validate(data)

    @classmethod
    def from_dict(cls, data: dict) -> "SuggestionSourceModel":
        return cls(**{key: data.get(key, "") for key in data.keys()})

    @classmethod
    def from_acteur(
        cls,
        acteur: Acteur | RevisionActeur | None,
        fields_to_include: list[str] | None = None,
    ) -> "SuggestionSourceModel":
        """
        Extract values from an Acteur or RevisionActeur instance
        using SuggestionSourceModel fields.
        Returns a SuggestionSourceModel instance with extracted values.
        Empty string is returned for missing or None values.
        """

        def get_field_from_code(
            acteur: Acteur | RevisionActeur, field_name: str
        ) -> str:
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
            if not prop_services:
                return ""
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

        def get_field_from_perimetre_adomicile_codes(
            acteur: Acteur | RevisionActeur,
        ) -> str:
            """Extract perimetre_adomicile_codes as JSON string."""
            perimetres = (
                list(acteur.perimetre_adomiciles.all())
                if hasattr(acteur, "perimetre_adomiciles")
                else []
            )
            if not perimetres:
                return ""
            return json.dumps(
                sorted(
                    [
                        {"type": perimetre.type, "valeur": perimetre.valeur}
                        for perimetre in perimetres
                    ],
                    key=lambda x: (x["type"], x["valeur"]),
                ),
                ensure_ascii=False,
            )

        def get_field_from_codes(
            acteur: Acteur | RevisionActeur, field_name: str
        ) -> str:
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
                )
                if m2m_objects
                else ""
            )

        if acteur is None:
            return cls()

        model_fields = SuggestionSourceModel.model_fields.keys()
        fields_to_process = (
            fields_to_include if fields_to_include else list(model_fields)
        )

        values = {}
        for field_name in fields_to_process:
            if field_name not in model_fields:
                raise ValueError(
                    f"Field {field_name} not found in SuggestionSourceModel"
                )
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

        return cls(**values)

    @classmethod
    def get_ordered_fields(cls) -> list[tuple[str]]:
        GROUPED_FIELDS = [("latitude", "longitude")]

        ordered_fields = []
        grouped_fields_processed = []
        for field in cls.model_fields:
            # get grouped_fields from field
            group_fields = next(
                (
                    grouped_field
                    for grouped_field in GROUPED_FIELDS
                    if field in grouped_field
                ),
                None,
            )
            if group_fields is not None:
                if group_fields not in grouped_fields_processed:
                    grouped_fields_processed.append(group_fields)
                    ordered_fields.append(group_fields)
                continue
            ordered_fields.append((field,))
        return ordered_fields

    @classmethod
    def get_not_editable_fields(cls) -> list[str]:
        """
        Returns the list of fields that are not editable.

        For now, we don't allow to update these fields because the values are specific
        """
        return [
            "acteur_service_codes",
            "identifiant_externe",
            "identifiant_unique",
            "label_codes",
            "proposition_service_codes",
            "source_code",
            "acteur_type_code",
            "perimetre_adomicile_codes",
        ]

    @classmethod
    def get_not_reportable_on_revision_fields(cls) -> list[str]:
        """
        Returns the list of fields that are not reportable on revisionacteur.

        - identifiants aren't reportable on revisionacteur
          because they are generated by the system.
        """
        return [
            "identifiant_externe",
            "identifiant_unique",
        ]

    @classmethod
    def get_not_reportable_on_parent_fields(cls) -> list[str]:
        """
        Returns the list of fields that are not reportable on parentrevisionacteur.

        - identifiants aren't reportable on parentrevisionacteur
          because they are generated by the system.
        - fields ending with _codes aren't reportable on parentrevisionacteur because
          they are inherited from the the children.
        """
        return [
            "acteur_service_codes",
            "identifiant_externe",
            "identifiant_unique",
            "label_codes",
            "proposition_service_codes",
            "perimetre_adomicile_codes",
        ]


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


def _suggestion_unitaires_to_suggestion_source_model(
    suggestion_unitaires: list[SuggestionUnitaire],
    model_name: str,
) -> SuggestionSourceModel:
    suggestion_unitaires_dict = {
        tuple(unit.champs): unit.valeurs
        for unit in suggestion_unitaires
        if unit.suggestion_modele == model_name
    }
    return SuggestionSourceModel.from_dict(
        _flatten_suggestion_unitaires(suggestion_unitaires_dict)
    )


def _get_ordered_fields_groups(
    suggestion_unitaires: list[SuggestionUnitaire],
) -> list[tuple]:
    all_suggestion_unitaires = {
        tuple(unit.champs): unit.valeurs for unit in suggestion_unitaires
    }
    fields_groups = list(set(all_suggestion_unitaires.keys()))
    ordered_fields = SuggestionSourceModel.get_ordered_fields()
    if any(fields not in ordered_fields for fields in fields_groups):
        raise ValueError(f"""fields in fields_groups are not in ORDERED_FIELDS:
                        {fields_groups=}
                        {ordered_fields=}""")
    return [fields for fields in ordered_fields if fields in fields_groups]


class SuggestionGroupeTypeSource(SuggestionGroupeType):
    """
    Represents a SuggestionGroupe of type SOURCE (AJOUT, MODIFICATION, SUPPRESSION)
    with all its SuggestionUnitaires, organized by target model.

    Encapsulates:
    - SuggestionSourceModel instances for each model's suggested changes
    - SuggestionSourceModel instances for each model's current DB values
    - The logic to build a ComparisonTable for UI rendering
    """

    display_tab: bool = True

    fields_groups: list[tuple[str, ...]]
    identifiant_unique: str

    acteur: Acteur | None = None
    revision_acteur: RevisionActeur | None = None
    parent_revision_acteur: RevisionActeur | None = None

    # Current DB values (extracted via SuggestionSourceModel.from_acteur)
    acteur_values: SuggestionSourceModel = SuggestionSourceModel()
    revision_acteur_values: SuggestionSourceModel = SuggestionSourceModel()
    parent_revision_acteur_values: SuggestionSourceModel = SuggestionSourceModel()

    # Suggested changes (extracted from SuggestionUnitaires)
    acteur_suggestions: SuggestionSourceModel = SuggestionSourceModel()
    revision_acteur_suggestions: SuggestionSourceModel = SuggestionSourceModel()
    parent_revision_acteur_suggestions: SuggestionSourceModel = SuggestionSourceModel()

    @classmethod
    def from_suggestion_groupe(
        cls, suggestion_groupe: SuggestionGroupe
    ) -> "SuggestionGroupeTypeSource":
        """
        Build a SuggestionGroupeTypeSource from a SuggestionGroupe.

        Raises ValueError if the type_action is not SOURCE_AJOUT,
        SOURCE_MODIFICATION, or SOURCE_SUPPRESSION.
        """

        type_action = suggestion_groupe.suggestion_cohorte.type_action

        source_actions = {
            SuggestionAction.SOURCE_AJOUT,
            SuggestionAction.SOURCE_MODIFICATION,
            SuggestionAction.SOURCE_SUPPRESSION,
        }
        if type_action not in source_actions:
            raise ValueError(
                f"SuggestionGroupe type_action must be one of {source_actions}, "
                f"got {type_action}"
            )

        suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())
        fields_groups = _get_ordered_fields_groups(suggestion_unitaires)
        flattened = [key for keys in fields_groups for key in keys]

        acteur_suggestions = _suggestion_unitaires_to_suggestion_source_model(
            suggestion_unitaires, "Acteur"
        )
        revision_acteur_suggestions = _suggestion_unitaires_to_suggestion_source_model(
            suggestion_unitaires, "RevisionActeur"
        )

        # SOURCE_AJOUT
        if type_action == SuggestionAction.SOURCE_AJOUT:
            identifiant_unique = (
                suggestion_groupe.get_identifiant_unique_from_suggestion_unitaires(
                    "Acteur"
                )
            )
            return cls(
                suggestion_groupe=suggestion_groupe,
                acteur=None,
                revision_acteur=None,
                parent_revision_acteur=None,
                fields_groups=fields_groups,
                identifiant_unique=identifiant_unique,
                acteur_suggestions=acteur_suggestions,
                revision_acteur_suggestions=revision_acteur_suggestions,
            )

        # SOURCE_MODIFICATION or SOURCE_SUPPRESSION
        acteur = suggestion_groupe.get_acteur_or_none()
        revision_acteur = suggestion_groupe.get_revision_acteur_or_none()
        parent_revision_acteur = suggestion_groupe.get_parent_revision_acteur_or_none()

        if not acteur:
            raise ValueError("acteur is required for non-SOURCE_AJOUT suggestions")

        parent_revision_acteur_suggestions = (
            _suggestion_unitaires_to_suggestion_source_model(
                suggestion_unitaires, "ParentRevisionActeur"
            )
        )

        return cls(
            suggestion_groupe=suggestion_groupe,
            acteur=acteur,
            revision_acteur=revision_acteur,
            parent_revision_acteur=parent_revision_acteur,
            fields_groups=fields_groups,
            identifiant_unique=acteur.identifiant_unique,
            acteur_values=SuggestionSourceModel.from_acteur(
                acteur, fields_to_include=flattened
            ),
            revision_acteur_values=SuggestionSourceModel.from_acteur(
                revision_acteur, fields_to_include=flattened
            ),
            parent_revision_acteur_values=SuggestionSourceModel.from_acteur(
                parent_revision_acteur, fields_to_include=flattened
            ),
            acteur_suggestions=acteur_suggestions,
            revision_acteur_suggestions=revision_acteur_suggestions,
            parent_revision_acteur_suggestions=parent_revision_acteur_suggestions,
        )

    # --- Display helpers ---

    @property
    def update_url(self) -> str:
        return reverse("data:suggestion_groupe", args=[self.suggestion_groupe.id])

    @property
    def acteur_change_url(self) -> str | None:
        return self.acteur.change_url if self.acteur else None

    @property
    def revision_acteur_change_url(self) -> str | None:
        return self.revision_acteur.change_url if self.revision_acteur else None

    @property
    def revision_acteur_displayedacteur_change_url(self) -> str | None:
        return (
            self.revision_acteur.displayedacteur_change_url
            if self.revision_acteur
            else None
        )

    @property
    def parent_revision_acteur_change_url(self) -> str | None:
        return (
            self.parent_revision_acteur.change_url
            if self.parent_revision_acteur
            else None
        )

    @property
    def parent_revision_acteur_displayedacteur_change_url(self) -> str | None:
        return (
            self.parent_revision_acteur.displayedacteur_change_url
            if self.parent_revision_acteur
            else None
        )

    @property
    def parent_revision_acteur_nombre_enfants(self) -> int | None:
        return (
            self.parent_revision_acteur.nombre_enfants
            if self.parent_revision_acteur
            else None
        )

    @property
    def has_parent_revision_acteur(self) -> bool:
        return self.parent_revision_acteur is not None

    @property
    def flattened_fields(self) -> list[str]:
        return [key for keys in self.fields_groups for key in keys]

    @property
    def fields_groups_json(self) -> str:
        return json.dumps(self.fields_groups)

    def _get_field_value(self, model: SuggestionSourceModel, field: str) -> str | None:
        value = getattr(model, field, None)
        return value if value else None

    def _target_values_json(self, fields: tuple[str, ...] | list[str]) -> str:
        return json.dumps(
            {
                field: getattr(self.acteur_suggestions, field)
                for field in fields
                if getattr(self.acteur_suggestions, field, None) is not None
            }
        )

    def _revision_replace_text(self, field: str) -> str:
        return (
            getattr(self.revision_acteur_suggestions, field, None)
            or getattr(self.acteur_suggestions, field, None)
            or ""
        )

    def _parent_replace_text(self, field: str) -> str:
        return (
            getattr(self.parent_revision_acteur_suggestions, field, None)
            or getattr(self.acteur_suggestions, field, None)
            or ""
        )

    def _source_display(self, field: str) -> str:
        return _display_suggestion_unitaire_for_a_field(
            field,
            self.acteur_suggestions,
            self._get_field_value(self.acteur_values, field),
        )

    def _revision_display(self, field: str) -> str:
        return _display_suggestion_unitaire_for_a_field(
            field,
            self.revision_acteur_suggestions,
            self._get_field_value(self.revision_acteur_values, field),
        )

    def _parent_display(self, field: str) -> str:
        return _display_suggestion_unitaire_for_a_field(
            field,
            self.parent_revision_acteur_suggestions,
            self._get_field_value(self.parent_revision_acteur_values, field),
        )

    # --- ComparisonTable builder helpers ---

    def _build_report_stimulus(
        self,
        fields: str,
        suggestion_modele: str,
        target_values_fields: tuple[str, ...] | list[str],
    ) -> StimulusControllerConfig:
        return StimulusControllerConfig(
            controller="report-update",
            values={
                "fields": fields,
                "suggestion-modele": suggestion_modele,
                "update-url": self.update_url,
                "target-values": self._target_values_json(target_values_fields),
                "fields-groups": self.fields_groups_json,
            },
            actions=["click->report-update#report"],
        )

    def _build_target_row_cells(
        self,
        field_group: tuple[str, ...],
        *,
        suggestion_modele: str,
        action_column_key: str,
        editable_column_key: str,
        action_icon: str,
        not_reportable: list[str],
        not_editable: list[str],
        display_fn,
        replace_text_fn,
        errors: dict | None,
    ) -> list[CellFieldsContent]:
        """Build the action cell + editable cell pair for a target model."""
        fields_str = "|".join(field_group)
        reportable = all(f not in not_reportable for f in field_group)

        action_cell = CellFieldsContent(
            column_key=action_column_key,
            cell_type="action",
            enabled=reportable,
            action_icon=action_icon,
            stimulus=(
                self._build_report_stimulus(fields_str, suggestion_modele, field_group)
                if reportable
                else None
            ),
        )

        editable_cell = CellFieldsContent(
            column_key=editable_column_key,
            cell_type="editable",
            fields=[
                CellField(
                    field_name=field,
                    display_html=display_fn(field),
                    editable=field not in not_editable,
                    stimulus=(
                        StimulusControllerConfig(
                            controller="cell-edit",
                            values={
                                "field": field,
                                "suggestion-modele": suggestion_modele,
                                "update-url": self.update_url,
                                "replace-text": replace_text_fn(field),
                                # TODO: may be json.dumps(field_group) is enough
                                "fields-groups": self.fields_groups_json,
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

        return [action_cell, editable_cell]

    # --- ComparisonTable builder ---

    def to_comparison_table(self, errors: dict | None = None) -> ComparisonTable:
        """Build a domain-agnostic ComparisonTable from this model's data."""
        not_editable = SuggestionSourceModel.get_not_editable_fields()
        not_reportable_revision = (
            SuggestionSourceModel.get_not_reportable_on_revision_fields()
        )
        not_reportable_parent = (
            SuggestionSourceModel.get_not_reportable_on_parent_fields()
        )
        flattened = self.flattened_fields

        # --- Columns ---
        columns = [
            ColumnHeader(key="label", css_classes="qf-w-1/4"),
            ColumnHeader(
                key="source",
                label="Acteur Importé",
                css_classes="qf-w-1/4",
                links=(
                    [HeaderLink(label="importé", url=self.acteur_change_url)]
                    if self.acteur_change_url
                    else []
                ),
            ),
            ColumnHeader(
                key="report_revision",
                label="▶️",
                css_classes="qf-text-center qf-text-2xl",
                header_action=self._build_report_stimulus(
                    "|".join(flattened), "RevisionActeur", flattened
                ),
            ),
        ]

        # Correction column
        correction_links = []
        if self.revision_acteur_change_url:
            correction_links.append(
                HeaderLink(label="corrigé", url=self.revision_acteur_change_url)
            )
            if not self.has_parent_revision_acteur:
                correction_links.append(
                    HeaderLink(
                        label="affiché",
                        url=self.revision_acteur_displayedacteur_change_url or "",
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
        if self.has_parent_revision_acteur:
            columns.append(
                ColumnHeader(
                    key="report_parent",
                    label="⏩",
                    css_classes="qf-text-center qf-text-2xl",
                    header_action=self._build_report_stimulus(
                        "|".join(flattened), "ParentRevisionActeur", flattened
                    ),
                )
            )
            columns.append(
                ColumnHeader(
                    key="parent",
                    label="Parent",
                    css_classes="qf-w-1/4",
                    links=[
                        HeaderLink(
                            label="corrigé",
                            url=self.parent_revision_acteur_change_url or "",
                        ),
                        HeaderLink(
                            label="affiché",
                            url=self.parent_revision_acteur_displayedacteur_change_url
                            or "",
                        ),
                    ],
                    subtitle=(
                        f"{self.parent_revision_acteur_nombre_enfants} enfants impactés"
                        if self.parent_revision_acteur_nombre_enfants
                        else None
                    ),
                )
            )

        # --- Rows ---
        rows = []
        for field_group in self.fields_groups:
            cells: list[CellFieldsContent | CellContent] = []

            # Source (display) cell
            cells.append(
                CellFieldsContent(
                    column_key="source",
                    cell_type="display",
                    fields=[
                        CellField(
                            field_name=field,
                            display_html=self._source_display(field),
                        )
                        for field in field_group
                    ],
                )
            )

            # Revision target cells (action + editable)
            cells.extend(
                self._build_target_row_cells(
                    field_group,
                    suggestion_modele="RevisionActeur",
                    action_column_key="report_revision",
                    editable_column_key="correction",
                    action_icon="▶️",
                    not_reportable=not_reportable_revision,
                    not_editable=not_editable,
                    display_fn=self._revision_display,
                    replace_text_fn=self._revision_replace_text,
                    errors=errors,
                )
            )

            # Parent target cells (conditional)
            if self.has_parent_revision_acteur:
                cells.extend(
                    self._build_target_row_cells(
                        field_group,
                        suggestion_modele="ParentRevisionActeur",
                        action_column_key="report_parent",
                        editable_column_key="parent",
                        action_icon="⏩",
                        not_reportable=not_reportable_parent,
                        not_editable=not_editable,
                        display_fn=self._parent_display,
                        replace_text_fn=self._parent_replace_text,
                        errors=errors,
                    )
                )

            rows.append(TableRow(label=", ".join(field_group), cells=cells))

        return ComparisonTable(columns=columns, rows=rows)

    def apply(self):
        acteur_data = self.acteur_suggestions.model_dump(exclude_none=True)
        if not acteur_data:
            raise ValueError("No acteur suggestion unitaires found")

        # Apply Acteur suggestions
        acteur = self._apply_one(Acteur, self.identifiant_unique, acteur_data)
        self._set_acteur_linked_objects(acteur, acteur_data)

        # Apply RevisionActeur suggestions
        revision_data = self.revision_acteur_suggestions.model_dump(exclude_none=True)
        if revision_data:
            identifiant_unique_revision = (
                self.revision_acteur.identifiant_unique
                if self.revision_acteur
                else self.identifiant_unique
            )
            revision_acteur = self._apply_one(
                RevisionActeur, identifiant_unique_revision, revision_data
            )
            self._set_acteur_linked_objects(revision_acteur, revision_data)

        # Apply ParentRevisionActeur suggestions
        parent_data = self.parent_revision_acteur_suggestions.model_dump(
            exclude_none=True
        )
        if parent_data and self.parent_revision_acteur:
            parent_acteur = self._apply_one(
                RevisionActeur,
                self.parent_revision_acteur.identifiant_unique,
                parent_data,
            )
            self._set_acteur_linked_objects(parent_acteur, parent_data)


SuggestionGroupeTypeSource.model_rebuild()
