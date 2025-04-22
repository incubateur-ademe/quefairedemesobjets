"""Generates the data stored in Suggestion.contexte field"""

import pandas as pd
from cluster.config.constants import COL_PARENT_ID_BEFORE
from utils import logging_utils as log


def suggestion_context_generate(
    df_cluster: pd.DataFrame,
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
) -> dict:
    """Generates a dict for use in Suggestion.contexte field"""
    from data.models.change import COL_CHANGE_MODEL_NAME
    from data.models.changes import ChangeActeurCreateAsParent

    clusters_cnt = df_cluster["cluster_id"].nunique()
    if clusters_cnt != 1:
        msg = f"We create contexte for 1 cluster at a time, got {clusters_cnt}"
        raise ValueError(msg)

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

    # Ensuring we have 1 exact group:
    exacts = df_cluster.groupby(cluster_fields_exact)
    groups = list(exacts.groups.keys())
    if len(groups) != 1:
        msg = f"""Champs exacts {cluster_fields_exact}={groups}
        n'est pas 1 groupe de valeur non vide"""
        log.preview("cluster problématique", df_cluster)
        raise ValueError(msg)

    result = {}
    result["exact_match"] = dict(zip(cluster_fields_exact, groups[0]))  # type: ignore
    cols = ["identifiant_unique"] + cluster_fields_fuzzy
    result["fuzzy_details"] = df_cluster[cols].to_dict(orient="records")

    return result
