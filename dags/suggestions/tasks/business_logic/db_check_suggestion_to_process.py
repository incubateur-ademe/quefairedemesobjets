from sources.config import shared_constants as constants
from utils.django import django_setup_full

django_setup_full()

from data.models import Suggestion  # noqa: E402


def get_suggestions_toprocess():
    return Suggestion.objects.prefetch_related("suggestion_cohorte").filter(
        statut=constants.SUGGESTION_ATRAITER
    )


def db_check_suggestion_to_process(**kwargs):
    suggestions = get_suggestions_toprocess()
    return suggestions.exists()
