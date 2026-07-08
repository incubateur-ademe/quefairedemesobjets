import json
import logging

from core.templatetags.admin_data_tags import display_diff_values
from data.models.comparison_table import (
    CellDisplayContent,
    CellEditableContent,
    CellHtmlContent,
    ColumnHeader,
    ComparisonTable,
    FieldInCell,
    LinkInCell,
    TableRow,
)
from data.models.suggestion import (
    SuggestionAction,
    SuggestionGroupe,
    SuggestionUnitaire,
)
from data.models.suggestions.abstract import (
    AE_ENTREPRISE_URL,
    AE_ETABLISSEMENT_URL,
    SuggestionGroupeType,
)
from django.contrib.admin.utils import quote
from django.urls import reverse
from qfdmo.models.acteur import Acteur, RevisionActeur

logger = logging.getLogger(__name__)


def _format_siret_label(siret: str) -> str:
    if not siret:
        return ""
    return (
        f'<a href="{AE_ETABLISSEMENT_URL}{siret}" target="_blank" '
        f'rel="noreferrer">{siret}</a>'
    )


def _format_siren_label(siren: str) -> str:
    if not siren:
        return ""
    return (
        f'<a href="{AE_ENTREPRISE_URL}{siren}" target="_blank" '
        f'rel="noreferrer">{siren}</a>'
    )


def _append_siret_to_row_label(row_label: str, siret: str) -> str:
    formatted_siret = _format_siret_label(siret)
    if not formatted_siret:
        return row_label
    return f"{row_label}<br/>SIRET&nbsp;: {formatted_siret}"


def _append_siren_to_row_label(row_label: str, siren: str) -> str:
    formatted_siren = _format_siren_label(siren)
    if not formatted_siren:
        return row_label
    return f"{row_label}<br/>SIREN&nbsp;: {formatted_siren}"


class SuggestionGroupeTypeEnrichMulti(SuggestionGroupeType):
    """
    Represents a SuggestionGroupe of type ENRICH_MULTI (CRAWL_URLS) with all its
    SuggestionUnitaires.

    Concerne when the Suggestion Groupe update a value for several acteurs.
    """

    @property
    def update_url(self) -> str:
        return reverse("data:suggestion_groupe", args=[self.suggestion_groupe.id])

    @classmethod
    def from_suggestion_groupe(
        cls, suggestion_groupe: SuggestionGroupe
    ) -> "SuggestionGroupeTypeEnrichMulti":
        return cls(suggestion_groupe=suggestion_groupe)

    def _get_fields_links(
        self,
        from_object: Acteur | RevisionActeur | None,
        suggestion_unitaire: SuggestionUnitaire,
    ) -> list[LinkInCell]:
        field_group = suggestion_unitaire.champs
        source_valeurs = [
            getattr(from_object, field) if from_object else None
            for field in field_group
        ]
        target_valeurs = suggestion_unitaire.valeurs

        return super()._get_fields_links(field_group, source_valeurs, target_valeurs)

    def _get_acteur_field_for_row_label(
        self,
        field_name: str,
        acteur: Acteur | None,
        revision_acteur: RevisionActeur | None,
        parent_revision_acteur: RevisionActeur | None,
    ) -> str:
        if parent_revision_acteur:
            return getattr(parent_revision_acteur, field_name)
        if revision_acteur and acteur:
            return getattr(revision_acteur, field_name) or getattr(acteur, field_name)
        if acteur:
            return getattr(acteur, field_name)
        raise ValueError(f"No value found for {field_name}")

    def _append_cohort_identifier_to_row_label(
        self,
        row_label: str,
        *,
        acteur: Acteur | None,
        revision_acteur: RevisionActeur | None,
        parent_revision_acteur: RevisionActeur | None,
    ) -> str:
        type_action = self.suggestion_groupe.suggestion_cohorte.type_action
        acteur_kwargs = {
            "acteur": acteur,
            "revision_acteur": revision_acteur,
            "parent_revision_acteur": parent_revision_acteur,
        }
        if type_action == SuggestionAction.ENRICH_ACTEURS_SIREN:
            return _append_siret_to_row_label(
                row_label,
                self._get_acteur_field_for_row_label("siret", **acteur_kwargs),
            )
        if type_action == SuggestionAction.ENRICH_ACTEURS_SIRET:
            return _append_siren_to_row_label(
                row_label,
                self._get_acteur_field_for_row_label("siren", **acteur_kwargs),
            )
        return row_label

    def to_comparison_table(self, errors: dict | None = None) -> ComparisonTable:
        suggestions_unitaires = self.suggestion_groupe.suggestion_unitaires.all()
        columns = [ColumnHeader(key="label")]

        for column_name in ["Champ(s)", "Acteur", "Correction"]:
            columns.append(
                ColumnHeader(
                    key=column_name,
                    label=column_name,
                )
            )
        rows = []
        for suggestion_unitaire in suggestions_unitaires:
            row_label = ""
            identifiant_unique = ""
            cells = []
            cells.append(
                CellHtmlContent(
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
                row_label = self._append_cohort_identifier_to_row_label(
                    row_label,
                    acteur=None,
                    revision_acteur=None,
                    parent_revision_acteur=parent_revision_acteur,
                )
                cells.append(
                    CellHtmlContent(
                        column_key="source",
                        html_content="🚫",
                    )
                )
                cells.append(
                    CellEditableContent(
                        column_key="update",
                        fields=[
                            FieldInCell(
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
                                suggestion_modele=suggestion_unitaire.suggestion_modele,
                                identifiant_unique=identifiant_unique,
                                update_url=self.update_url,
                                replace_text=valeur,
                                fields_groups=json.dumps([(champ,)]),
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
                        links=self._get_fields_links(
                            from_object=parent_revision_acteur,
                            suggestion_unitaire=suggestion_unitaire,
                        ),
                    )
                )
            else:
                identifiant_unique = suggestion_unitaire.revision_acteur_id
                revision_acteur = (
                    RevisionActeur.objects.filter(
                        identifiant_unique=identifiant_unique
                    ).first()
                    if suggestion_unitaire.revision_acteur_id
                    else None
                )
                acteur = suggestion_unitaire.acteur or Acteur.objects.get(
                    identifiant_unique=identifiant_unique
                )
                row_label = f"Acteur {identifiant_unique}"
                row_label = self._append_cohort_identifier_to_row_label(
                    row_label,
                    acteur=acteur,
                    revision_acteur=revision_acteur,
                    parent_revision_acteur=None,
                )

                cells.append(
                    CellDisplayContent(
                        column_key="source",
                        fields=[
                            FieldInCell(
                                field_name=champ,
                                display_html=getattr(acteur, champ),
                            )
                            for champ in suggestion_unitaire.champs
                        ],
                    )
                )
                cells.append(
                    CellEditableContent(
                        column_key="update",
                        fields=[
                            FieldInCell(
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
                                suggestion_modele=suggestion_unitaire.suggestion_modele,
                                update_url=self.update_url,
                                replace_text=valeur,
                                fields_groups=json.dumps([(champ,)]),
                                identifiant_unique=identifiant_unique,
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
                        links=self._get_fields_links(
                            from_object=revision_acteur,
                            suggestion_unitaire=suggestion_unitaire,
                        ),
                    )
                )

            # suggestion_unitaire.suggestion_modele == "ParentRevisionActeur"
            links = []
            if suggestion_unitaire.suggestion_modele == "ParentRevisionActeur":
                links.append(
                    LinkInCell(
                        label="Parent",
                        url=reverse(
                            "qfdmo:getorcreate_revisionacteur",
                            args=[quote(identifiant_unique)],
                        ),
                    )
                )
            else:
                links.append(
                    LinkInCell(
                        label="Source",
                        url=reverse(
                            "admin:qfdmo_acteur_change",
                            args=[quote(identifiant_unique)],
                        ),
                    )
                )
                links.append(
                    LinkInCell(
                        label="Correction",
                        url=reverse(
                            "qfdmo:getorcreate_revisionacteur",
                            args=[identifiant_unique],
                        ),
                    )
                )
            label_cell = CellHtmlContent(
                column_key="label",
                html_content=row_label,
                links=links,
            )
            rows.append(TableRow(cells=[label_cell, *cells]))

        return ComparisonTable(columns=columns, rows=rows)

    def apply(self):
        suggestion_groupe = self.suggestion_groupe

        # Acteur suggestions
        for acteur_suggestion_unitaire in suggestion_groupe.suggestion_unitaires.all():
            if acteur_suggestion_unitaire.suggestion_modele == "RevisionActeur":
                identifiant_unique = (
                    acteur_suggestion_unitaire.revision_acteur_id
                    or acteur_suggestion_unitaire.acteur_id
                )
                if not identifiant_unique:
                    raise ValueError(
                        "No identifiant_unique found for acteur_suggestion_unitaire"
                        f" {acteur_suggestion_unitaire}"
                    )
                acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
                revision_acteur = acteur.get_or_create_revision()
                acteur_data = {
                    champ: valeur
                    for champ, valeur in zip(
                        acteur_suggestion_unitaire.champs,
                        acteur_suggestion_unitaire.valeurs,
                    )
                }

                revision_acteur = self._apply_one(
                    RevisionActeur, identifiant_unique, acteur_data
                )
                self._set_acteur_linked_objects(revision_acteur, acteur_data)

            elif acteur_suggestion_unitaire.suggestion_modele == "ParentRevisionActeur":
                identifiant_unique = (
                    acteur_suggestion_unitaire.parent_revision_acteur_id
                )
                if not identifiant_unique:
                    raise ValueError(
                        "No identifiant_unique found for acteur_suggestion_unitaire"
                        f" {acteur_suggestion_unitaire}"
                    )
                parent_revision_acteur = RevisionActeur.objects.get(
                    identifiant_unique=identifiant_unique
                )
                parent_revision_acteur_data = {
                    champ: valeur
                    for champ, valeur in zip(
                        acteur_suggestion_unitaire.champs,
                        acteur_suggestion_unitaire.valeurs,
                    )
                }
                parent_revision_acteur = self._apply_one(
                    RevisionActeur,
                    identifiant_unique,
                    parent_revision_acteur_data,
                )
                self._set_acteur_linked_objects(
                    parent_revision_acteur, parent_revision_acteur_data
                )
