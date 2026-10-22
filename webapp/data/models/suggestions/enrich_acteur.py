from data.models.comparison_table import ComparisonTable, TableRow
from data.models.suggestion import SuggestionAction, SuggestionGroupe
from data.models.suggestions.enrich_multi import SuggestionGroupeTypeEnrichMulti
from data.models.suggestions.source import (
    SuggestionGroupeTypeSource,
    SuggestionSourceModel,
    _get_ordered_fields_groups,
    _suggestion_unitaires_to_suggestion_source_model,
)

# Columns of the SOURCE ComparisonTable not displayed for these suggestions
REPORT_COLUMN_KEYS = ["report_revision", "report_parent"]

# SuggestionCohorte.type_action handled by SuggestionGroupeTypeEnrichActeur
ENRICH_ACTEUR_TYPE_ACTIONS = [
    SuggestionAction.ENRICH_ACTEURS_CLOSED,
    SuggestionAction.ENRICH_ACTEURS_RGPD,
]


class SuggestionGroupeTypeEnrichActeur(SuggestionGroupeTypeSource):
    """
    Represents a SuggestionGroupe of type ENRICH_ACTEURS_CLOSED or
    ENRICH_ACTEURS_RGPD: 1 SuggestionGroupe per acteur and 1 SuggestionUnitaire
    per field.

    Displayed like the SOURCE suggestions, without the tabs nor the report
    columns; the changes can be edited on the parent if it exists.
    """

    display_tab: bool = False

    @classmethod
    def from_suggestion_groupe(
        cls, suggestion_groupe: SuggestionGroupe
    ) -> "SuggestionGroupeTypeEnrichActeur":
        type_action = suggestion_groupe.suggestion_cohorte.type_action
        if type_action not in ENRICH_ACTEUR_TYPE_ACTIONS:
            raise ValueError(
                f"SuggestionGroupe type_action must be one of "
                f"{ENRICH_ACTEUR_TYPE_ACTIONS}, got {type_action}"
            )

        suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())
        fields_groups = _get_ordered_fields_groups(suggestion_unitaires)
        flattened = [key for keys in fields_groups for key in keys]

        acteur = suggestion_groupe.get_acteur_or_none()
        revision_acteur = suggestion_groupe.get_revision_acteur_or_none()
        parent_revision_acteur = suggestion_groupe.get_parent_revision_acteur_or_none()

        # The acteur may only exist as a parent (no Acteur nor RevisionActeur)
        acteur_or_parent = acteur or revision_acteur or parent_revision_acteur
        if not acteur_or_parent:
            raise ValueError("acteur, revision_acteur or parent is required")

        return cls(
            suggestion_groupe=suggestion_groupe,
            acteur=acteur,
            revision_acteur=revision_acteur,
            parent_revision_acteur=parent_revision_acteur,
            fields_groups=fields_groups,
            identifiant_unique=acteur_or_parent.identifiant_unique,
            acteur_values=SuggestionSourceModel.from_acteur(
                acteur, fields_to_include=flattened
            ),
            revision_acteur_values=SuggestionSourceModel.from_acteur(
                revision_acteur, fields_to_include=flattened
            ),
            parent_revision_acteur_values=SuggestionSourceModel.from_acteur(
                parent_revision_acteur, fields_to_include=flattened
            ),
            acteur_suggestions=_suggestion_unitaires_to_suggestion_source_model(
                suggestion_unitaires, "Acteur"
            ),
            revision_acteur_suggestions=(
                _suggestion_unitaires_to_suggestion_source_model(
                    suggestion_unitaires, "RevisionActeur"
                )
            ),
            parent_revision_acteur_suggestions=(
                _suggestion_unitaires_to_suggestion_source_model(
                    suggestion_unitaires, "ParentRevisionActeur"
                )
            ),
        )

    def to_comparison_table(self, errors: dict | None = None) -> ComparisonTable:
        """Same table as the SOURCE suggestions, without the report columns
        (▶️ / ⏩): the changes are already suggested on their target model, and
        can be edited in the correction and parent columns"""
        table = super().to_comparison_table(errors=errors)
        return ComparisonTable(
            columns=[
                column
                for column in table.columns
                if column.key not in REPORT_COLUMN_KEYS
            ],
            rows=[
                TableRow(
                    cells=[
                        cell
                        for cell in row.cells
                        if cell.column_key not in REPORT_COLUMN_KEYS
                    ]
                )
                for row in table.rows
            ],
        )

    def apply(self):
        # 1 SuggestionUnitaire per field, applied on its own model (Acteur,
        # RevisionActeur or ParentRevisionActeur)
        SuggestionGroupeTypeEnrichMulti.from_suggestion_groupe(
            self.suggestion_groupe
        ).apply()


SuggestionGroupeTypeEnrichActeur.model_rebuild()
