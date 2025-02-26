import logging

from crawl.config.constants import LABEL_URL_ORIGINE
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def crawl_urls_suggestions_to_db(
    metadata: dict,
    suggestions: list[dict],
    identifiant_action: str,
    identifiant_execution: str,
) -> None:
    """Writing suggestions to DB

    Args:
        df_clusters (pd.DataFrame): clusters for metadata purposes
        suggestions (list[dict]): suggestions, 1 per cluster
        identifiant_action (str): ex: Airflow dag_id
        identifiant_execution (str): ex: Airflow run_id
    """

    logger.info(f"{identifiant_action=}")
    logger.info(f"{identifiant_execution=}")

    from data.models import (
        Suggestion,
        SuggestionAction,
        SuggestionCohorte,
        SuggestionStatut,
    )

    cohorte = SuggestionCohorte(
        identifiant_action=identifiant_action,
        identifiant_execution=identifiant_execution,
        type_action=SuggestionAction.CRAWL_URLS,
        statut=SuggestionStatut.AVALIDER,
        metadata=metadata,
    )
    cohorte.save()

    for sugg in suggestions:
        url = sugg["contexte"][LABEL_URL_ORIGINE]
        log.preview(f"Suggestion pour {url=}", sugg)
        Suggestion(
            suggestion_cohorte=cohorte,
            statut=SuggestionStatut.AVALIDER,
            contexte=sugg["contexte"],
            suggestion=sugg["suggestion"],
        ).save()
