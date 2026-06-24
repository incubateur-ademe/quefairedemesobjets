from django_tasks import task

from data.models.suggestion import SuggestionGroupe


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


@task()
def apply_suggestions_to_parent_task(suggestion_groupe_ids: list[int]) -> None:
    """Apply suggestions to the parent for each given SuggestionGroupe.

    Runs in the background via django-tasks. Takes ids (not a queryset) because
    the task may run in a separate process and re-fetches inside.
    """
    for sg in SuggestionGroupe.objects.filter(id__in=suggestion_groupe_ids):
        if sg.suggestions_can_be_applied_to_parent():
            _update_or_copy_acteur_suggestions_to_target(
                sg,
                target_modele="ParentRevisionActeur",
                target_fk_field="parent_revision_acteur_id",
                target_fk_id=sg.parent_revision_acteur_id,
            )


@task()
def apply_suggestions_to_correction_task(suggestion_groupe_ids: list[int]) -> None:
    """Apply suggestions to the acteur correction for each given SuggestionGroupe."""
    for sg in SuggestionGroupe.objects.filter(id__in=suggestion_groupe_ids):
        if sg.suggestions_can_be_applied_to_correction():
            _update_or_copy_acteur_suggestions_to_target(
                sg,
                target_modele="RevisionActeur",
                target_fk_field="revision_acteur_id",
                target_fk_id=(sg.revision_acteur_id or sg.acteur_id),
            )
