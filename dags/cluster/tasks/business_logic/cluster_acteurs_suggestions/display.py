import pandas as pd
from utils.django import django_setup_full

django_setup_full()


def cluster_acteurs_suggestions_display(
    df_clusters: pd.DataFrame,
) -> list[dict]:
    """Generate suggestion changes from a df of clusters. At
    this stage we don't work with the Cohorte & Suggestion models
    as there require DB interactions. We focus on preparing the
    suggestion changes as a list of dict which we'll send to DB
    in a later step.

    Args:
        df_clusters (pd.DataFrame): clusters to generate changes from

    Returns:
        pd.DataFrame: a df where each row represents 1 suggestion
        containing a "changes" column with a list of changes
    """

    from data.models.change import (
        COL_CHANGE_MODEL_NAME,
        COL_CHANGE_MODEL_PARAMS,
        COL_CHANGE_ORDER,
        COL_CHANGE_REASON,
    )
    from data.models.change_models import ChangeActeurUpdateParentId

    suggestions = []
    # One suggestion per cluster, multiple changes per suggestion
    for cluster_id, cluster in df_clusters.groupby("cluster_id"):
        changes = []
        for _, row in cluster.iterrows():
            # What every change has in common
            change = {
                COL_CHANGE_ORDER: row[COL_CHANGE_ORDER],
                COL_CHANGE_REASON: row[COL_CHANGE_REASON],
                COL_CHANGE_MODEL_NAME: row[COL_CHANGE_MODEL_NAME],
            }
            # Switching to context of a change model to keep things short
            name = row[COL_CHANGE_MODEL_NAME]

            # All acteur-related changes have an "identifiant_unique"
            params = {"identifiant_unique": row["identifiant_unique"]}

            # Then for each model we construct the necessary data
            if name == ChangeActeurUpdateParentId.name():
                params["data"] = {"parent_id": row["parent_id"]}

            change[COL_CHANGE_MODEL_PARAMS] = params
            changes.append(change)

        changes.append(change)
        suggestions.append({"cluster_id": cluster_id, "changes": changes})

    return suggestions
