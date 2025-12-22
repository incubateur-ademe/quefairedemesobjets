import logging

from django.db import IntegrityError, transaction
from sources.config import shared_constants as constants
from suggestions.tasks.business_logic.db_check_suggestion_to_process import (
    get_suggestions_toprocess,
)
from tenacity import retry, retry_if_exception_type, stop_after_attempt

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(IntegrityError))
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
            suggestion.metadata = {
                "error": e.args[0] if e.args else str(e),
            }
            suggestion.statut = constants.SUGGESTION_ERREUR
            suggestion.save()
