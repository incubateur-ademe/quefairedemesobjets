import logging

from django.db import transaction
from sources.config import shared_constants as constants
from suggestions.tasks.business_logic.db_check_suggestion_to_process import (
    get_suggestions_toprocess,
)

logger = logging.getLogger(__name__)


def suggestion_apply_atomic(suggestion):
    with transaction.atomic():
        suggestion.apply()


def db_apply_suggestion(use_suggestion_groupe: bool = False):
    suggestions = get_suggestions_toprocess(use_suggestion_groupe=use_suggestion_groupe)

    for suggestion in suggestions:
        try:
            suggestion.statut = constants.SUGGESTION_ENCOURS
            suggestion.save()

            # Apply suggestion here
            suggestion_apply_atomic(suggestion)

            suggestion.statut = constants.SUGGESTION_SUCCES
            suggestion.save()

        except Exception as e:
            logger.warning(
                f"Error while applying suggestion {suggestion.id} - {type(e)}: {e}"
            )
            suggestion.statut = constants.SUGGESTION_ERREUR
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
