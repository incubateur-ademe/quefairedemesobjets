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
    context["exact_match"] = dict(zip(cluster_fields_exact, groups[0]))  # type: ignore
    context["fuzzy_details"] = df_cluster[cols].to_dict(orient="records")

    return context
