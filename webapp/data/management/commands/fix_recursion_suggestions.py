import argparse
import copy

from data.models.changes import ChangeActeurCreateAsParent, ChangeActeurKeepAsParent
from data.models.suggestion import Suggestion, SuggestionStatut
from django.core.management.base import BaseCommand

# Message stored in Suggestion.metadata["error"] when a suggestion failed with a
# RecursionError. The root cause is a parent acteur whose change data carries a
# `parent` / `parent_id` pointing to itself: applying it makes the parent FK
# self-referential and any later load recurse infinitely through
# RevisionActeur.__init__.
RECURSION_ERROR_MESSAGE = "maximum recursion depth exceeded"

# A parent acteur must never have a parent: these keys are illegal in the data of
# a "keep/create as parent" change and are what triggered the recursion.
ILLEGAL_PARENT_KEYS = ["parent", "parent_id"]

PARENT_CHANGE_MODEL_NAMES = [
    ChangeActeurKeepAsParent.name(),
    ChangeActeurCreateAsParent.name(),
]


class Command(BaseCommand):
    help = (
        "Fix CLUSTERING suggestions that ended in error with "
        f"'{RECURSION_ERROR_MESSAGE}' by removing the self-referential parent "
        "from their parent changes, then re-queue them for processing."
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
        parser.add_argument(
            "--suggestion-cohorte-id",
            type=int,
            help="Restrict the fix to suggestions from this cohort id",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        requeue = options["requeue"]
        suggestion_cohorte_id = options["suggestion_cohorte_id"]

        suggestions = Suggestion.objects.filter(
            statut=SuggestionStatut.ERREUR,
            metadata__error__icontains=RECURSION_ERROR_MESSAGE,
        )
        if suggestion_cohorte_id is not None:
            suggestions = suggestions.filter(
                suggestion_cohorte_id=suggestion_cohorte_id
            )

        total = suggestions.count()
        cohort_msg = (
            f" (cohorte {suggestion_cohorte_id})" if suggestion_cohorte_id else ""
        )
        self.stdout.write(
            f"{total} suggestion(s) en erreur avec "
            f"'{RECURSION_ERROR_MESSAGE}'{cohort_msg}"
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

            new_changes = copy.deepcopy(changes)
            removed = self._strip_illegal_parents(suggestion.id, new_changes)

            if not removed:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Suggestion {suggestion.id}: aucune clé parent "
                        "auto-référente trouvée, à inspecter manuellement"
                    )
                )
                continue

            fixed_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Suggestion {suggestion.id}: {removed} clé(s) parent "
                    "supprimée(s)"
                )
            )

            if not dry_run:
                suggestion.suggestion["changes"] = new_changes
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

    def _strip_illegal_parents(self, suggestion_id, changes: list) -> int:
        """Remove self-referential parent keys from parent changes in place.

        Returns the number of keys removed."""
        removed = 0
        for change in changes:
            if not isinstance(change, dict):
                continue
            if change.get("model_name") not in PARENT_CHANGE_MODEL_NAMES:
                continue
            model_params = change.get("model_params") or {}
            data = model_params.get("data")
            if not isinstance(data, dict):
                continue
            for key in ILLEGAL_PARENT_KEYS:
                if key in data:
                    del data[key]
                    removed += 1
        return removed
