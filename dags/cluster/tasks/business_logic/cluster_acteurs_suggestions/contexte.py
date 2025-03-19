"""Generates the data stored in Suggestion.contexte field"""

import pandas as pd
from cluster.config.constants import COL_PARENT_ID_BEFORE


def suggestion_contexte_generate(
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

    # We exclude parents-to-be-created as by definition they
    # don't exist yet so they can't be part of context as to how
    # we generated the suggestion in the first place
    df_cluster = df_cluster[
        df_cluster[COL_CHANGE_MODEL_NAME] != ChangeActeurCreateAsParent.name()
    ]
    # We exclude existing children because these were are as-is
    # purely based on their previous parent_id. Right now if we include
    # them here they can break the exacts.groups.keys() == 1 check because:
    # - they might be missing data (Revisions only have changes)
    # - we didn't do ANY normalization on them since they are re-attached as-is
    # Once we introduce the feature to re-cluster children:
    # - the issue will naturally go away (beacuse we will be forced to process them)
    # - TODO: we will need to make the below exclusion conditional on above feature
    df_cluster = df_cluster[df_cluster[COL_PARENT_ID_BEFORE].isnull()]

    # Ensuring we have 1 exact group:
    # - intentionally NOT dropping NAs (we shouldn't have any)
    #   to detect potential errors
    exacts = df_cluster.groupby(cluster_fields_exact, dropna=False)
    groups = list(exacts.groups.keys())
    if len(groups) != 1:
        msg = f"We should have 1 exact group, got {groups}"
        raise ValueError(msg)

    result = {}
    result["exact_match"] = dict(zip(cluster_fields_exact, groups[0]))  # type: ignore
    cols = ["id"] + cluster_fields_fuzzy
    result["fuzzy_details"] = df_cluster[cols].to_dict(orient="records")

    return result
