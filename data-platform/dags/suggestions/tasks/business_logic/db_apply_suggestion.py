import logging

from django.db import transaction
from suggestions.tasks.business_logic.db_check_suggestion_to_process import (
    get_suggestions_toprocess,
)

logger = logging.getLogger(__name__)


def suggestion_apply_atomic(suggestion):
    with transaction.atomic():
        suggestion.apply()


def db_apply_suggestion(use_suggestion_groupe: bool = False):
    from data.models.suggestion import SuggestionStatut

    suggestions = get_suggestions_toprocess(use_suggestion_groupe=use_suggestion_groupe)

    for suggestion in suggestions:
        try:
            suggestion.statut = SuggestionStatut.ENCOURS
            suggestion.save()

            # Apply suggestion here
            suggestion_apply_atomic(suggestion)

            suggestion.statut = SuggestionStatut.SUCCES
            suggestion.save()

        except Exception as e:
            logger.warning(
                f"Error while applying suggestion {suggestion.id} - {type(e)}: {e}"
            )
            suggestion.statut = SuggestionStatut.ERREUR
            try:
                suggestion.metadata = {
                    "error": e.args[0] if e.args else str(e),
                }
                suggestion.save()
            except Exception:
                # if the serialization fails, we use just the string representation
                suggestion.metadata = {
                    "error": str(e),
                }
                suggestion.save()
