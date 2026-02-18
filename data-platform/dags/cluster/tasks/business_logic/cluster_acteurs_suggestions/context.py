"""Generates the data stored in Suggestion.contexte field"""

import logging

import pandas as pd
from cluster.config.constants import COL_PARENT_ID_BEFORE
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def suggestion_context_generate(
    df_cluster: pd.DataFrame,
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
) -> dict | None:
    """Generates a dict for use in Suggestion.contexte field"""
    from data.models.change import COL_CHANGE_MODEL_NAME
    from data.models.changes import ChangeActeurCreateAsParent

    cluster_ids = df_cluster["cluster_id"].unique()
    if len(cluster_ids) != 1:
        msg = f"We create contexte for 1 cluster at a time, got {cluster_ids=}"
        raise ValueError(msg)
    cluster_id = cluster_ids[0]

    # Exclude parents-to-be-created as non-existing thus not part of clustering context
    df_cluster = df_cluster[
        df_cluster[COL_CHANGE_MODEL_NAME] != ChangeActeurCreateAsParent.name()
    ]
    # E existing children because currently integrated as-is based on their
    # previous parent_id. Right now if we include them they can break
    # the exacts.groups.keys() == 1 check because:
    # - they might be missing data (Revisions only have changes)
    # - we didn't do ANY normalization on them
    # Once we introduce the feature to re-cluster children:
    # - above issue will naturally go away (because we will be forced to process them)
    # - TODO: we will need to make the below exclusion conditional on feature activation
    df_cluster = df_cluster[df_cluster[COL_PARENT_ID_BEFORE].isnull()]

    # Can happen when DAG to refresh displayed acteurs wasn't ran:
    # - we can have data in displayed but in reality underlying acteurs
    # are not longer ACTIVE nor present (e.g. removed parents)
    if df_cluster.empty:
        msg = f"{cluster_id=} vide: bien rafraîchir les acteurs affichés"
        logger.warning(msg)
        return None

    # Ensuring we have 1 exact group:
    exacts = df_cluster.groupby(cluster_fields_exact)
    groups = list(exacts.groups.keys())
    if len(groups) != 1:
        msg = f"""Champs exacts {cluster_fields_exact}={groups}
        n'est pas 1 groupe de valeur non vide"""
        log.preview("cluster problématique", df_cluster)
        raise ValueError(msg)

    cols = ["identifiant_unique"] + cluster_fields_fuzzy
    context = {}
    context["cluster_id"] = cluster_id
    # Make sure groups[0] is always a tuple, even with a single field
    group_val = groups[0] if isinstance(groups[0], tuple) else (groups[0],)
    context["exact_match"] = dict(zip(cluster_fields_exact, group_val))  # type: ignore
    context["fuzzy_details"] = df_cluster[cols].to_dict(orient="records")

    return context
