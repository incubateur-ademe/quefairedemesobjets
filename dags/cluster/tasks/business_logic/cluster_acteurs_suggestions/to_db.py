import logging

import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_suggestions.contexte import (
    suggestion_contexte_generate,
)
from cluster.tasks.business_logic.misc.df_metadata_get import df_metadata_get
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def cluster_acteurs_suggestions_to_db(
    df_clusters: pd.DataFrame,
    suggestions: list[dict],
    identifiant_action: str,
    identifiant_execution: str,
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
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
        type_action=SuggestionAction.CLUSTERING,
        statut=SuggestionStatut.AVALIDER,
        metadata=df_metadata_get(df_clusters),
    )
    cohorte.save()

    for sugg_dict in suggestions:
        # cluster = df_clusters[df_clusters["cluster_id"] == sugg_dict["cluster_id"]]
        cluster_id = sugg_dict["cluster_id"]
        df_cluster = df_clusters[df_clusters["cluster_id"] == cluster_id]

        sugg_obj = Suggestion(
            suggestion_cohorte=cohorte,
            statut=SuggestionStatut.AVALIDER,
            # FIXME:
            # This is causing serialization issues due to certain values
            # being of Django type (e.g. ActeurType)
            # contexte=cluster.to_dict(orient="records"),
            contexte=suggestion_contexte_generate(
                df_cluster=df_cluster,
                cluster_fields_exact=cluster_fields_exact,
                cluster_fields_fuzzy=cluster_fields_fuzzy,
            ),
            suggestion=sugg_dict,
        )
        log.preview(f"{cluster_id=} suggestion dict", sugg_dict)
        sugg_obj.save()
