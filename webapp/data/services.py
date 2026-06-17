"""Reusable business logic shared between the Django admin and the cohorte
review endpoints, so neither duplicates the other."""

from data.models.suggestion import SuggestionGroupe, SuggestionUnitaire
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Exists, OuterRef, Q
from djangoql.exceptions import DjangoQLSchemaError
from djangoql.schema import BoolField, DjangoQLSchema, IntField, StrField


def _update_or_copy_acteur_suggestions_to_target(
    suggestion_groupe: SuggestionGroupe,
    *,
    target_modele: str,
    target_fk_field: str,
    target_fk_id: int | None,
) -> None:
    """For each SuggestionUnitaire « Acteur » of the group, update the existing
    target SuggestionUnitaire (same `champs` and same target) if it exists,
    otherwise create a new one by cloning the source suggestion.

    `target_fk_field` is the name of the FK field (ex: "revision_acteur_id" or
    "parent_revision_acteur_id") that points to the target entity.
    """
    suggestion_unitaires = list(suggestion_groupe.suggestion_unitaires.all())
    acteur_sources = [
        su for su in suggestion_unitaires if su.suggestion_modele == "Acteur"
    ]

    for acteur_source in acteur_sources:
        target_suggestion = next(
            (
                su
                for su in suggestion_unitaires
                if su.suggestion_modele == target_modele
                and getattr(su, target_fk_field) == target_fk_id
                and su.champs == acteur_source.champs
            ),
            None,
        )
        if target_suggestion:
            target_suggestion.valeurs = acteur_source.valeurs
        else:
            target_suggestion = acteur_source
            target_suggestion.id = None
            target_suggestion.suggestion_modele = target_modele
            setattr(target_suggestion, target_fk_field, target_fk_id)
        target_suggestion.save()


def apply_suggestions_to_parent(suggestion_groupe: SuggestionGroupe) -> bool:
    """Copy/update the groupe's Acteur suggestions onto its parent revision.

    Returns True when the groupe was eligible and processed."""
    if not suggestion_groupe.suggestions_can_be_applied_to_parent():
        return False
    _update_or_copy_acteur_suggestions_to_target(
        suggestion_groupe,
        target_modele="ParentRevisionActeur",
        target_fk_field="parent_revision_acteur_id",
        target_fk_id=suggestion_groupe.parent_revision_acteur_id,
    )
    return True


def apply_suggestions_to_correction(suggestion_groupe: SuggestionGroupe) -> bool:
    """Copy/update the groupe's Acteur suggestions onto its revision (correction).

    Returns True when the groupe was eligible and processed."""
    if not suggestion_groupe.suggestions_can_be_applied_to_correction():
        return False
    _update_or_copy_acteur_suggestions_to_target(
        suggestion_groupe,
        target_modele="RevisionActeur",
        target_fk_field="revision_acteur_id",
        target_fk_id=(
            suggestion_groupe.revision_acteur_id or suggestion_groupe.acteur_id
        ),
    )
    return True


class SuggestionQLSchemaMixin(DjangoQLSchema):
    """Force JSON/Array fields to be string fields for text search."""

    def get_fields(self, model):
        fields = super().get_fields(model)
        result = []
        for field in fields:
            field_name = field if isinstance(field, str) else field.name
            model_field = model._meta.get_field(field_name)
            if model_field and (
                isinstance(model_field, models.JSONField)
                or isinstance(model_field, ArrayField)
            ):
                field = StrField(name=field_name)
            result.append(field)
        return result


class HasSuggestionUnitaireWithChampField(StrField):
    """Permet de filtrer par champ de suggestion unitaire individuel"""

    name = "has_suggestion_unitaire_with_champ"
    suggest_options = False

    def get_lookup(self, path, operator, value):
        if operator not in {"~", "!~"}:
            raise DjangoQLSchemaError(
                f'Field "{self.name}" only supports "~" and "!~" operators'
            )

        has_matching_suggestion_unitaire = Exists(
            SuggestionUnitaire.objects.filter(
                suggestion_groupe_id=OuterRef("pk"),
                champs__icontains=value,
            )
        )
        q = Q(has_matching_suggestion_unitaire)
        return ~q if operator == "!~" else q


class SuggestionGroupeQLSchema(SuggestionQLSchemaMixin):
    """DjangoQL schema for SuggestionGroupe exposing the custom annotated
    fields. The searched queryset MUST carry
    `.with_suggestion_unitaire_count().with_has_parent().with_has_correction()`
    annotations for these fields to resolve."""

    def get_fields(self, model):
        fields = super().get_fields(model)

        if model == SuggestionGroupe:
            return [
                *[
                    field
                    for field in fields
                    if field not in ["suggestion_unitaires_count"]
                ],
                IntField(name="suggestion_unitaires_count"),
                BoolField(name="has_parent"),
                BoolField(name="has_correction"),
            ] + [HasSuggestionUnitaireWithChampField()]

        return fields
