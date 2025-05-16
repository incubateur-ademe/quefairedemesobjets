import logging

from acteurs.tasks.business_logic.db_check_suggestion_to_process import (
    get_suggestions_toprocess,
)
from django.db import transaction
from sources.config import shared_constants as constants

logger = logging.getLogger(__name__)


def db_apply_suggestion():
    suggestions = get_suggestions_toprocess()

    for suggestion in suggestions:
        try:
            suggestion.statut = constants.SUGGESTION_ENCOURS
            suggestion.save()

            # Apply suggestion here
            with transaction.atomic():
                suggestion.apply()

            suggestion.statut = constants.SUGGESTION_SUCCES
            suggestion.save()

        except Exception as e:
            logger.warning(f"Error while applying suggestion {suggestion.id}: {e}")
            suggestion.metadata = {
                "error": e.args[0] if e.args else str(e),
            }
            suggestion.statut = constants.SUGGESTION_ERREUR
            suggestion.save()
