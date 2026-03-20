import json

from core.templatetags.admin_data_tags import display_diff_values
from data.models.comparison_table import (
    CellContent,
    CellField,
    CellFieldsContent,
    ColumnHeader,
    ComparisonTable,
    StimulusControllerConfig,
    TableRow,
)
from data.models.suggestion import SuggestionGroupe
from django.urls import reverse
from pydantic import BaseModel, ConfigDict


class SuggestionGroupeTypeEnrichMulti(BaseModel):
    """
    Represents a SuggestionGroupe of type ENRICH_MULTI (CRAWL_URLS) with all its
    SuggestionUnitaires.

    Concerne when the Suggestion Groupe update a value for several acteurs.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    suggestion_groupe: SuggestionGroupe

    @property
    def update_url(self) -> str:
        return reverse("data:suggestion_groupe", args=[self.suggestion_groupe.id])

    @classmethod
    def from_suggestion_groupe(
        cls, suggestion_groupe: SuggestionGroupe
    ) -> "SuggestionGroupeTypeEnrichMulti":
        return cls(suggestion_groupe=suggestion_groupe)

    def to_comparison_table(self, errors: dict | None = None) -> ComparisonTable:
        suggestions_unitaires = self.suggestion_groupe.suggestion_unitaires.all()

        columns = [ColumnHeader(key="label", css_classes="qf-w-1/4")]

        for column_name in ["Champ(s)", "Acteur", "Mise à jour"]:
            columns.append(
                ColumnHeader(
                    key=column_name,
                    label=column_name,
                    css_classes="qf-w-1/4",
                )
            )
        rows = []
        for suggestion_unitaire in suggestions_unitaires:
            row_label = ""
            cells = []
            cells.append(
                CellContent(
                    column_key="source",
                    html_content=f"{", ".join(suggestion_unitaire.champs)}",
                )
            )
            if suggestion_unitaire.suggestion_modele == "ParentRevisionActeur":
                identifiant_unique = (
                    suggestion_unitaire.parent_revision_acteur.identifiant_unique
                )
                parent_revision_acteur = suggestion_unitaire.parent_revision_acteur
                row_label = f"Parent {identifiant_unique}"
                cells.append(
                    CellContent(
                        column_key="source",
                        html_content="🚫",
                    )
                )
                cells.append(
                    CellFieldsContent(
                        column_key="update",
                        cell_type="editable",
                        fields=[
                            CellField(
                                field_name=champ,
                                display_html=display_diff_values(
                                    (
                                        getattr(parent_revision_acteur, champ)
                                        if parent_revision_acteur
                                        else ""
                                    ),
                                    valeur,
                                ),
                                editable=True,
                                stimulus=(
                                    StimulusControllerConfig(
                                        controller="cell-edit",
                                        values={
                                            "field": champ,
                                            "suggestion-modele": (
                                                suggestion_unitaire.suggestion_modele
                                            ),
                                            "identifiant-unique": identifiant_unique,
                                            "update-url": self.update_url,  # TODO
                                            "replace-text": valeur,
                                            "fields-groups": json.dumps([(champ,)]),
                                        },
                                        actions=[
                                            "blur->cell-edit#save",
                                            "focus->cell-edit#replace",
                                        ],
                                    )
                                ),
                                error=(
                                    str(errors.get(champ, ""))
                                    if errors and errors.get(champ)
                                    else None
                                ),
                            )
                            for champ, valeur in zip(
                                suggestion_unitaire.champs, suggestion_unitaire.valeurs
                            )
                        ],
                    )
                )
            else:
                identifiant_unique = (
                    suggestion_unitaire.revision_acteur.identifiant_unique
                    if suggestion_unitaire.revision_acteur
                    else suggestion_unitaire.acteur.identifiant_unique
                )
                row_label = f"Acteur {identifiant_unique}"
                acteur = suggestion_unitaire.acteur
                revision_acteur = suggestion_unitaire.revision_acteur

                cells.append(
                    CellFieldsContent(
                        column_key="source",
                        cell_type="display",
                        fields=[
                            CellField(
                                field_name=champ,
                                display_html=getattr(acteur, champ),
                            )
                            for champ in suggestion_unitaire.champs
                        ],
                    )
                )
                cells.append(
                    CellFieldsContent(
                        column_key="update",
                        cell_type="editable",
                        fields=[
                            CellField(
                                field_name=champ,
                                display_html=display_diff_values(
                                    (
                                        getattr(revision_acteur, champ)
                                        if revision_acteur
                                        else getattr(acteur, champ)
                                    ),
                                    valeur,
                                ),
                                editable=True,
                                stimulus=(
                                    StimulusControllerConfig(
                                        controller="cell-edit",
                                        values={
                                            "field": champ,
                                            "suggestion-modele": (
                                                suggestion_unitaire.suggestion_modele
                                            ),
                                            "update-url": self.update_url,  # TODO
                                            "replace-text": valeur,
                                            "fields-groups": json.dumps([(champ,)]),
                                            "identifiant-unique": identifiant_unique,
                                        },
                                        actions=[
                                            "blur->cell-edit#save",
                                            "focus->cell-edit#replace",
                                        ],
                                    )
                                ),
                                error=(
                                    str(errors.get(champ, ""))
                                    if errors and errors.get(champ)
                                    else None
                                ),
                            )
                            for champ, valeur in zip(
                                suggestion_unitaire.champs, suggestion_unitaire.valeurs
                            )
                        ],
                    )
                )

            rows.append(
                TableRow(
                    label=row_label,
                    cells=cells,
                )
            )

        return ComparisonTable(columns=columns, rows=rows)
