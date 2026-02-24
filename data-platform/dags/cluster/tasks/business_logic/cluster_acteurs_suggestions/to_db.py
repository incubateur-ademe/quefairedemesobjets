import logging

import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_suggestions.context import (
    suggestion_context_generate,
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
    # For context purposes only
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
) -> None:
    """Writing suggestions to DB"""

    logger.info(f"{identifiant_action=}")
    logger.info(f"{identifiant_execution=}")

    from data.models.suggestion import (
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
        # TODO: refactor this DAG to generate suggestions & context
        # at the same time like we do for latest DAGs (BAN, AE etc..)
        # which would allow getting all data from context and not mismatch
        # context & changes
        cluster_id = sugg_dict["cluster_id"]
        logger.info(f"suggestion {cluster_id=}")
        df_cluster = df_clusters[df_clusters["cluster_id"] == cluster_id]

        # Fixed following PR1501 but comment/raise to help debug in case of regression
        if df_cluster.empty:
            msg = "Cluster vide = présent en suggestion mais plus dans df_clusters!!!"
            raise ValueError(msg)

        # TODO: do the context + suggestion changes generation at once
        # just like for latest DAGs (BAN, AE etc..) to avoid mismatch
        # and hacks like the one below
        contexte = suggestion_context_generate(
            df_cluster=df_cluster,
            cluster_fields_exact=cluster_fields_exact,
            cluster_fields_fuzzy=cluster_fields_fuzzy,
        )
        if contexte is None:
            continue
        sugg_obj = Suggestion(
            suggestion_cohorte=cohorte,
            statut=SuggestionStatut.AVALIDER,
            contexte=contexte,
            suggestion=sugg_dict,
        )
        log.preview(f"{cluster_id=} suggestion dict", sugg_dict)
        sugg_obj.save()
