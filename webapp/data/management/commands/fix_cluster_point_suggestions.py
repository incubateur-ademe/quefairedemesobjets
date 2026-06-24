import argparse

from data.models.changes import (
    ChangeActeurCreateAsParent,
    ChangeActeurKeepAsParent,
    ChangeActeurUpdateParentId,
)
from data.models.suggestion import Suggestion, SuggestionStatut
from django.core.management.base import BaseCommand
from qfdmo.models.acteur import DEFAULT_SOURCE_CODE, VueActeur

# Message stored in Suggestion.metadata["error"] when a CLUSTERING suggestion
# failed because the parent's location could not be rebuilt.
POINT_ERROR_MESSAGE = "Invalid parameters given for Point initialization"

# Change models that describe the parent acteur (the one carrying the broken
# location / acteur_type data).
PARENT_CHANGE_MODEL_NAMES = [
    ChangeActeurKeepAsParent.name(),
    ChangeActeurCreateAsParent.name(),
]


class Command(BaseCommand):
    help = (
        "Fix CLUSTERING suggestions that ended in error with "
        f"'{POINT_ERROR_MESSAGE}' by rebuilding the parent's longitude / latitude "
        "and acteur_type from its children (preferring the "
        f"'{DEFAULT_SOURCE_CODE}' source), then re-queue them for processing."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Run command without writing changes to the database",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        parser.add_argument(
            "--requeue",
            help="Reset fixed suggestions to ATRAITER so the DAG reprocesses them",
            action=argparse.BooleanOptionalAction,
            default=True,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        requeue = options["requeue"]

        suggestions = Suggestion.objects.filter(
            statut=SuggestionStatut.ERREUR,
            metadata__error__icontains=POINT_ERROR_MESSAGE,
        )

        total = suggestions.count()
        self.stdout.write(
            f"{total} suggestion(s) en erreur avec '{POINT_ERROR_MESSAGE}'"
        )

        fixed_count = 0
        for suggestion in suggestions:
            changes = self._extract_changes(suggestion)
            if changes is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Suggestion {suggestion.id}: pas de 'changes' "
                        "exploitable, ignorée"
                    )
                )
                continue

            parent_change = self._find_parent_change(changes)
            if parent_change is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Suggestion {suggestion.id}: pas de changement parent, "
                        "ignorée"
                    )
                )
                continue

            child = self._pick_child(changes)
            if child is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Suggestion {suggestion.id}: aucun enfant avec une "
                        "localisation exploitable, à inspecter manuellement"
                    )
                )
                continue

            data = parent_change["model_params"]["data"]
            self._apply_child_data(data, child)

            fixed_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Suggestion {suggestion.id}: corrigée depuis l'enfant "
                    f"{child.identifiant_unique} (source "
                    f"{child.source.code if child.source else '?'})"
                )
            )

            if not dry_run:
                suggestion.suggestion["changes"] = changes
                if requeue:
                    suggestion.statut = SuggestionStatut.ATRAITER
                    suggestion.metadata = None
                suggestion.save()

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}{fixed_count}/{total} suggestion(s) corrigée(s)"
                + (" et remises à ATRAITER" if requeue and not dry_run else "")
            )
        )

    def _extract_changes(self, suggestion) -> list | None:
        suggestion_data = suggestion.suggestion
        if not isinstance(suggestion_data, dict):
            return None
        changes = suggestion_data.get("changes")
        if not isinstance(changes, list):
            return None
        return changes

    def _find_parent_change(self, changes: list) -> dict | None:
        for change in changes:
            if not isinstance(change, dict):
                continue
            if change.get("model_name") not in PARENT_CHANGE_MODEL_NAMES:
                continue
            model_params = change.get("model_params")
            if isinstance(model_params, dict) and isinstance(
                model_params.get("data"), dict
            ):
                return change
        return None

    def _child_ids(self, changes: list) -> list[str]:
        """Children are the acteurs re-pointed to the new parent, in order."""
        ids = []
        for change in changes:
            if not isinstance(change, dict):
                continue
            if change.get("model_name") != ChangeActeurUpdateParentId.name():
                continue
            child_id = (change.get("model_params") or {}).get("id")
            if child_id is not None:
                ids.append(child_id)
        return ids

    def _pick_child(self, changes: list) -> VueActeur | None:
        """Return the first child carrying a usable location, prioritizing the
        'communautelvao' source, then the order they appear in the suggestion."""
        child_ids = self._child_ids(changes)
        if not child_ids:
            return None

        acteurs = VueActeur.objects.filter(
            identifiant_unique__in=child_ids
        ).select_related("acteur_type", "source")
        by_id = {a.identifiant_unique: a for a in acteurs}

        # Keep the suggestion order, but move communautelvao children first
        ordered = [by_id[cid] for cid in child_ids if cid in by_id]
        ordered.sort(
            key=lambda a: 0 if a.source and a.source.code == DEFAULT_SOURCE_CODE else 1
        )

        for acteur in ordered:
            if acteur.location is not None:
                return acteur
        return None

    def _apply_child_data(self, data: dict, child: VueActeur) -> None:
        # A serialized location is split into longitude / latitude (no Point over
        # JSON), so we never keep a raw `location` key around.
        data.pop("location", None)
        data["longitude"] = child.location.x
        data["latitude"] = child.location.y
        if child.acteur_type is not None:
            data["acteur_type"] = child.acteur_type.code
