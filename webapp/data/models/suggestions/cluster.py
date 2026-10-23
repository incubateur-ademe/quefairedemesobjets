import json
import logging

from core.templatetags.admin_data_tags import display_diff_values
from data.models.changes import (
    ChangeActeurCreateAsParent,
    ChangeActeurDeleteAsParent,
    ChangeActeurKeepAsParent,
    ChangeActeurUpdateParentId,
    ChangeActeurVerifyRevision,
)
from data.models.comparison_table import (
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
from data.models.suggestions.abstract import SuggestionGroupeType
from django.contrib.admin.utils import quote
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models as django_models
from django.urls import reverse
from django.utils.html import escape, format_html
from qfdmo.models.acteur import Acteur, DisplayedActeur, RevisionActeur

logger = logging.getLogger(__name__)

# SuggestionCohorte.type_action handled by SuggestionGroupeTypeCluster
CLUSTER_TYPE_ACTIONS = [SuggestionAction.CLUSTERING]

CREATE_AS_PARENT = ChangeActeurCreateAsParent.name()
KEEP_AS_PARENT = ChangeActeurKeepAsParent.name()
UPDATE_PARENT_ID = ChangeActeurUpdateParentId.name()
VERIFY_REVISION = ChangeActeurVerifyRevision.name()
DELETE_AS_PARENT = ChangeActeurDeleteAsParent.name()

PARENT_CHANGES = [CREATE_AS_PARENT, KEEP_AS_PARENT]
PARENT_ID_CHANGES = [UPDATE_PARENT_ID, VERIFY_REVISION]

ROLES = {
    CREATE_AS_PARENT: "🆕 Parent à créer",
    KEEP_AS_PARENT: "1️⃣ Parent conservé",
    UPDATE_PARENT_ID: "🔀 À rattacher au parent",
    VERIFY_REVISION: "🟰 Déjà enfant du parent",
    DELETE_AS_PARENT: "🔴 Parent à supprimer",
}

# Pin color on the map, by change
MAP_COLORS = {
    CREATE_AS_PARENT: "blue",
    KEEP_AS_PARENT: "blue",
    UPDATE_PARENT_ID: "green",
    VERIFY_REVISION: "grey",
    DELETE_AS_PARENT: "red",
}

COORDINATES_FIELDS = ["latitude", "longitude"]


def _as_str(value) -> str:
    return "" if value is None else str(value)


def _cast_parent_valeur(champ: str, valeur: str):
    """SuggestionUnitaire.valeurs are strings (written by the DAG or edited in
    the UI), cast them to the RevisionActeur field type"""
    if champ in COORDINATES_FIELDS:
        return float(valeur) if valeur != "" else None
    try:
        field = RevisionActeur._meta.get_field(champ)
    except FieldDoesNotExist:
        return valeur
    if valeur == "":
        return None if field.null or field.is_relation else ""
    if isinstance(field, django_models.ForeignKey):
        return field.target_field.to_python(valeur)
    if field.is_relation:
        # e.g. perimetre_adomiciles, serialized as JSON by the DAG
        return json.loads(valeur)
    return field.to_python(valeur)


class SuggestionGroupeTypeCluster(SuggestionGroupeType):
    """
    Represents a SuggestionGroupe of type CLUSTERING: 1 SuggestionGroupe per
    cluster, the chosen parent being the parent_revision_acteur.

    SuggestionUnitaires (see dags cluster to_db_groupes):
    - ParentRevisionActeur, 1 per field of the parent to create or keep
    - RevisionActeur parent_id, for the acteurs to point to the parent and for
      the acteurs already children of the parent (no change unless edited to
      empty, to detach the acteur)
    - ParentRevisionActeur without field, for the parents to delete
    The change to apply is stored in SuggestionUnitaire.parametres
    """

    suggestion_unitaires: list[SuggestionUnitaire]
    acteurs_by_id: dict[str, Acteur] = {}
    revision_acteurs_by_id: dict[str, RevisionActeur] = {}
    displayed_acteurs_by_id: dict[str, DisplayedActeur] = {}

    @classmethod
    def from_suggestion_groupe(
        cls, suggestion_groupe: SuggestionGroupe
    ) -> "SuggestionGroupeTypeCluster":
        type_action = suggestion_groupe.suggestion_cohorte.type_action
        if type_action not in CLUSTER_TYPE_ACTIONS:
            raise ValueError(
                f"SuggestionGroupe type_action must be one of "
                f"{CLUSTER_TYPE_ACTIONS}, got {type_action}"
            )
        suggestion_unitaires = list(
            suggestion_groupe.suggestion_unitaires.order_by("ordre", "id")
        )
        ids = {_su_identifiant_unique(su) for su in suggestion_unitaires} | {
            acteur["identifiant_unique"]
            for acteur in (suggestion_groupe.contexte or {}).get("acteurs", [])
        }
        return cls(
            suggestion_groupe=suggestion_groupe,
            suggestion_unitaires=suggestion_unitaires,
            acteurs_by_id=Acteur.objects.select_related(
                "source", "acteur_type"
            ).in_bulk(ids),
            revision_acteurs_by_id=RevisionActeur.objects.select_related(
                "source", "acteur_type"
            ).in_bulk(ids),
            displayed_acteurs_by_id=DisplayedActeur.objects.select_related(
                "source", "acteur_type"
            ).in_bulk(ids),
        )

    @property
    def update_url(self) -> str:
        return reverse("data:suggestion_groupe", args=[self.suggestion_groupe.id])

    @property
    def contexte(self) -> dict:
        return self.suggestion_groupe.contexte or {}

    @property
    def parent_id(self) -> str | None:
        return self.suggestion_groupe.parent_revision_acteur_id

    @property
    def cluster_fields(self) -> list[str]:
        return self.contexte.get("cluster_fields_exact", []) + self.contexte.get(
            "cluster_fields_fuzzy", []
        )

    @property
    def snapshots_by_id(self) -> dict[str, dict]:
        """Acteurs as read by the DAG"""
        return {
            acteur["identifiant_unique"]: acteur
            for acteur in self.contexte.get("acteurs", [])
        }

    def _changes(self) -> list[tuple[str, str, list[SuggestionUnitaire]]]:
        """(change_model_name, identifiant_unique, suggestion_unitaires) in the
        order the changes must be applied"""
        changes: dict[tuple[str, str], list[SuggestionUnitaire]] = {}
        for su in self.suggestion_unitaires:
            change_model_name = su.parametres.get("change_model_name")
            if change_model_name not in ROLES:
                raise ValueError(f"Unexpected change_model_name: {change_model_name}")
            key = (change_model_name, _su_identifiant_unique(su))
            changes.setdefault(key, []).append(su)
        return [(name, id, sus) for (name, id), sus in changes.items()]

    def _parent_suggested_data(self) -> dict[str, str]:
        return {
            champ: valeur
            for change_model_name, _, sus in self._changes()
            if change_model_name in PARENT_CHANGES
            for su in sus
            for champ, valeur in zip(su.champs, su.valeurs)
        }

    def _value(self, identifiant_unique: str, field: str):
        """Current value: revision if filled, else acteur, else as read by the
        DAG (e.g. displayed acteur), else suggested (parent to create)"""
        for instance in [
            self.revision_acteurs_by_id.get(identifiant_unique),
            self.acteurs_by_id.get(identifiant_unique),
            self.displayed_acteurs_by_id.get(identifiant_unique),
        ]:
            value = getattr(instance, field, None) if instance else None
            if value not in [None, ""]:
                return value
        value = self.snapshots_by_id.get(identifiant_unique, {}).get(field)
        if value not in [None, ""]:
            return value
        if identifiant_unique == self.parent_id:
            return self._parent_suggested_data().get(field)
        return None

    def _links(self, identifiant_unique: str) -> list[LinkInCell]:
        links = []
        acteur = self.acteurs_by_id.get(identifiant_unique)
        revision_acteur = self.revision_acteurs_by_id.get(identifiant_unique)
        displayed_acteur = self.displayed_acteurs_by_id.get(identifiant_unique)
        if acteur:
            links.append(
                LinkInCell(
                    label="importé",
                    url=reverse(
                        "admin:qfdmo_acteur_change", args=[quote(identifiant_unique)]
                    ),
                )
            )
        if revision_acteur:
            links.append(
                LinkInCell(
                    label="corrigé" if acteur else "parent",
                    url=reverse(
                        "admin:qfdmo_revisionacteur_change",
                        args=[quote(identifiant_unique)],
                    ),
                )
            )
        if displayed_acteur:
            links.append(
                LinkInCell(
                    label="affiché",
                    url=reverse(
                        "admin:qfdmo_displayedacteur_change",
                        args=[quote(identifiant_unique)],
                    ),
                )
            )
            links.append(
                LinkInCell(
                    label="fiche",
                    url=reverse("qfdmo:acteur-detail", args=[displayed_acteur.uuid]),
                )
            )
        return links

    def _parent_id_cell(
        self,
        identifiant_unique: str,
        suggestion_unitaire: SuggestionUnitaire | None,
        errors: dict | None,
    ) -> CellHtmlContent | CellEditableContent:
        if suggestion_unitaire is None:
            return CellHtmlContent(column_key="parent_after", html_content="-")
        revision_acteur = self.revision_acteurs_by_id.get(identifiant_unique)
        current = _as_str(revision_acteur.parent_id if revision_acteur else None)
        valeur = suggestion_unitaire.valeurs[0] if suggestion_unitaire.valeurs else ""
        if valeur == current:
            display_html = escape(valeur)
        elif valeur == "":
            display_html = "∅ détaché du cluster"
        else:
            display_html = display_diff_values(current, valeur)
        return CellEditableContent(
            column_key="parent_after",
            fields=[
                FieldInCell(
                    field_name="parent_id",
                    display_html=display_html,
                    editable=True,
                    suggestion_modele=suggestion_unitaire.suggestion_modele,
                    identifiant_unique=identifiant_unique,
                    update_url=self.update_url,
                    replace_text=valeur,
                    fields_groups=json.dumps([["parent_id"]]),
                    error=(
                        str(errors.get("parent_id"))
                        if errors and errors.get("parent_id")
                        else None
                    ),
                )
            ],
        )

    def to_comparison_table(self, errors: dict | None = None) -> ComparisonTable:
        """1 row per acteur of the cluster: parent, children, parents to delete"""
        exact_fields = self.contexte.get("cluster_fields_exact", [])
        columns = [
            ColumnHeader(key="label", label="Acteur"),
            ColumnHeader(key="role", label="Rôle"),
            ColumnHeader(key="source", label="Source / Type"),
            ColumnHeader(key="statut", label="Statut"),
            ColumnHeader(key="nombre_enfants", label="Enfants"),
            ColumnHeader(key="parent_before", label="Parent actuel"),
            ColumnHeader(key="parent_after", label="Parent après (éditable)"),
        ] + [
            ColumnHeader(
                key=f"field_{field}",
                label=field,
                subtitle="🎯 exact" if field in exact_fields else "〰️ fuzzy",
            )
            for field in self.cluster_fields
        ]

        rows = []
        for change_model_name, identifiant_unique, sus in self._changes():
            raison = sus[0].raison
            parent_id_su = next((su for su in sus if su.champs == ["parent_id"]), None)
            revision_acteur = self.revision_acteurs_by_id.get(identifiant_unique)
            source = self._value(identifiant_unique, "source")
            acteur_type = self._value(identifiant_unique, "acteur_type")
            nombre_enfants = (
                revision_acteur.nombre_enfants
                if revision_acteur
                else self.snapshots_by_id.get(identifiant_unique, {}).get(
                    "nombre_enfants"
                )
            )
            cells = [
                CellHtmlContent(
                    column_key="label",
                    html_content=format_html(
                        "<strong>{}</strong><br/><small>{}</small>",
                        _as_str(self._value(identifiant_unique, "nom")),
                        identifiant_unique,
                    ),
                    links=self._links(identifiant_unique),
                ),
                CellHtmlContent(
                    column_key="role",
                    html_content=format_html(
                        "{}<br/><small>{}. {}</small>",
                        ROLES[change_model_name],
                        sus[0].ordre,
                        raison,
                    ),
                ),
                CellHtmlContent(
                    column_key="source",
                    html_content=format_html(
                        "{}<br/>{}",
                        _as_str(getattr(source, "code", source)) or "-",
                        _as_str(getattr(acteur_type, "code", acteur_type)) or "-",
                    ),
                ),
                CellHtmlContent(
                    column_key="statut",
                    html_content=escape(
                        _as_str(self._value(identifiant_unique, "statut")) or "-"
                    ),
                ),
                CellHtmlContent(
                    column_key="nombre_enfants",
                    html_content=escape(_as_str(nombre_enfants)),
                ),
                CellHtmlContent(
                    column_key="parent_before",
                    html_content=escape(
                        _as_str(revision_acteur.parent_id if revision_acteur else None)
                        or "-"
                    ),
                ),
                self._parent_id_cell(identifiant_unique, parent_id_su, errors),
            ] + [
                CellHtmlContent(
                    column_key=f"field_{field}",
                    html_content=escape(
                        _as_str(self._value(identifiant_unique, field)) or "-"
                    ),
                )
                for field in self.cluster_fields
            ]
            rows.append(TableRow(cells=cells))

        return ComparisonTable(columns=columns, rows=rows)

    def to_parent_comparison_table(self, errors: dict | None = None) -> ComparisonTable:
        """1 row per field suggested on the parent to create or keep"""
        parent_revision_acteur = self.revision_acteurs_by_id.get(self.parent_id or "")
        columns = [
            ColumnHeader(key="champs", label="Champ(s)"),
            ColumnHeader(key="current", label="Parent actuel"),
            ColumnHeader(key="update", label="Parent après (éditable)"),
        ]
        rows = []
        for change_model_name, identifiant_unique, sus in self._changes():
            if change_model_name not in PARENT_CHANGES:
                continue
            for su in sus:
                if not su.champs:
                    continue
                currents = [
                    _as_str(getattr(parent_revision_acteur, champ, None))
                    for champ in su.champs
                ]
                rows.append(
                    TableRow(
                        cells=[
                            CellHtmlContent(
                                column_key="champs",
                                html_content=escape(", ".join(su.champs)),
                            ),
                            CellHtmlContent(
                                column_key="current",
                                html_content=(
                                    escape(", ".join(currents))
                                    if parent_revision_acteur
                                    else "🚫"
                                ),
                            ),
                            CellEditableContent(
                                column_key="update",
                                fields=[
                                    FieldInCell(
                                        field_name=champ,
                                        display_html=display_diff_values(
                                            current, valeur
                                        ),
                                        editable=True,
                                        suggestion_modele=su.suggestion_modele,
                                        identifiant_unique=identifiant_unique,
                                        update_url=self.update_url,
                                        replace_text=valeur,
                                        fields_groups=json.dumps([su.champs]),
                                        error=(
                                            str(errors.get(champ))
                                            if errors and errors.get(champ)
                                            else None
                                        ),
                                    )
                                    for champ, valeur, current in zip(
                                        su.champs, su.valeurs, currents
                                    )
                                ],
                            ),
                        ]
                    )
                )
        return ComparisonTable(columns=columns, rows=rows)

    def map_points(self) -> list[dict]:
        points = []
        for change_model_name, identifiant_unique, _ in self._changes():
            latitude = self._value(identifiant_unique, "latitude")
            longitude = self._value(identifiant_unique, "longitude")
            if latitude in [None, ""] or longitude in [None, ""]:
                continue
            points.append(
                {
                    "key": f"cluster-{identifiant_unique}",
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "color": MAP_COLORS[change_model_name],
                    "draggable": False,
                    "text": "P" if change_model_name in PARENT_CHANGES else "",
                }
            )
        return points

    def update_suggestion_unitaire(
        self, suggestion_modele: str, identifiant_unique: str, fields_values: dict
    ) -> dict | None:
        """Update the valeurs of the edited SuggestionUnitaire, returns the
        errors if any"""
        for champ, valeur in fields_values.items():
            valeur = _as_str(valeur).strip()
            su = next(
                (
                    su
                    for su in self.suggestion_unitaires
                    if su.suggestion_modele == suggestion_modele
                    and _su_identifiant_unique(su) == identifiant_unique
                    and champ in su.champs
                ),
                None,
            )
            if su is None:
                return {champ: f"Pas de suggestion {champ} pour {identifiant_unique}"}

            if champ == "parent_id":
                # Empty = detach the acteur from the cluster
                if (
                    valeur
                    and valeur != self.parent_id
                    and not RevisionActeur.objects.filter(pk=valeur).exists()
                ):
                    return {champ: f"Parent {valeur} inexistant"}
            else:
                try:
                    _cast_parent_valeur(champ, valeur)
                except (ValueError, TypeError, ValidationError) as e:
                    return {champ: f"Valeur invalide pour {champ}: {e}"}

            valeurs = list(su.valeurs)
            valeurs[su.champs.index(champ)] = valeur
            su.valeurs = valeurs
            su.save()
        return None

    def _apply_parent_id(self, identifiant_unique: str, parent_id: str):
        revision_acteur = RevisionActeur.objects.filter(pk=identifiant_unique).first()
        if revision_acteur and revision_acteur.parent_id == parent_id:
            ChangeActeurVerifyRevision(id=identifiant_unique).apply()
        else:
            ChangeActeurUpdateParentId(
                id=identifiant_unique, data={"parent_id": parent_id}
            ).apply()

    @staticmethod
    def _detach(identifiant_unique: str):
        revision_acteur = RevisionActeur.objects.filter(pk=identifiant_unique).first()
        if revision_acteur and revision_acteur.parent_id:
            revision_acteur.parent = None
            revision_acteur.save()

    def apply(self):
        # Acteurs detached from the cluster (parent_id emptied in the UI) are
        # detached once the other acteurs point to the parent, otherwise the
        # parent could be deleted for lack of children, but before deleting the
        # former parents which must not have children anymore
        detached_ids = []
        for change_model_name, identifiant_unique, sus in self._changes():
            data = {
                champ: valeur
                for su in sus
                for champ, valeur in zip(su.champs, su.valeurs)
            }
            if change_model_name == DELETE_AS_PARENT:
                for detached_id in detached_ids:
                    self._detach(detached_id)
                detached_ids = []

            if change_model_name in PARENT_CHANGES:
                change_model = (
                    ChangeActeurCreateAsParent
                    if change_model_name == CREATE_AS_PARENT
                    else ChangeActeurKeepAsParent
                )
                parent_data = {
                    champ: _cast_parent_valeur(champ, valeur)
                    for champ, valeur in data.items()
                }
                # Same as data_serialize: no location rather than an empty one
                if any(parent_data.get(champ) is None for champ in COORDINATES_FIELDS):
                    for champ in COORDINATES_FIELDS:
                        parent_data.pop(champ, None)
                change_model(id=identifiant_unique, data=parent_data).apply()
            elif change_model_name in PARENT_ID_CHANGES:
                parent_id = data.get("parent_id", "").strip()
                if parent_id:
                    self._apply_parent_id(identifiant_unique, parent_id)
                else:
                    detached_ids.append(identifiant_unique)
            elif change_model_name == DELETE_AS_PARENT:
                ChangeActeurDeleteAsParent(id=identifiant_unique).apply()

        for detached_id in detached_ids:
            self._detach(detached_id)


def _su_identifiant_unique(suggestion_unitaire: SuggestionUnitaire) -> str:
    return (
        suggestion_unitaire.revision_acteur_id
        or suggestion_unitaire.acteur_id
        or suggestion_unitaire.parent_revision_acteur_id
        or ""
    )


SuggestionGroupeTypeCluster.model_rebuild()
