from sources.config import shared_constants as constants
from utils.django import django_setup_full

django_setup_full()


# Here we get only the suggestion with AVALIDER status
# ENCOURS status is for suggestion that are being processed, it can remain sommes
# suggestions with this status after process it if Airflow cluster shutdown suddenly
# in this case w would like to inspect what happened and before reprocess it


def get_suggestions_toprocess(use_suggestion_groupe: bool = False):
    from data.models.suggestion import Suggestion, SuggestionGroupe

    cls = Suggestion
    if use_suggestion_groupe:
        cls = SuggestionGroupe

    return cls.objects.prefetch_related("suggestion_cohorte").filter(
        statut=constants.SUGGESTION_ATRAITER
    )


def db_check_suggestion_to_process(use_suggestion_groupe: bool = False, **kwargs):
    suggestions = get_suggestions_toprocess(use_suggestion_groupe=use_suggestion_groupe)
    return suggestions.exists()
