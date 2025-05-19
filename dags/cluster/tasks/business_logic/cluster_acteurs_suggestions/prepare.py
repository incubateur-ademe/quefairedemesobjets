import logging

import pandas as pd
from cluster.config.constants import COL_PARENT_DATA_NEW

from utils import logging_utils as log
from utils.data_serialize_reconstruct import data_serialize
from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()


def cluster_changes_get(cluster: pd.DataFrame) -> list[dict]:
    """Generate changes for 1 cluster suggestion"""
    from data.models.change import (
        COL_CHANGE_MODEL_NAME,
        COL_CHANGE_MODEL_PARAMS,
        COL_CHANGE_ORDER,
        COL_CHANGE_REASON,
        SuggestionChange,
    )
    from data.models.changes import (
        ChangeActeurCreateAsParent,
        ChangeActeurDeleteAsParent,
        ChangeActeurKeepAsParent,
        ChangeActeurUpdateParentId,
        ChangeActeurVerifyRevision,
    )
    from qfdmo.models.acteur import RevisionActeur

    # Building changes for each acteur in the cluster
    changes = []
    for _, row in cluster.iterrows():

        # Common params
        row = row.to_dict()
        model_name = row[COL_CHANGE_MODEL_NAME]
        model_params = {"id": row["identifiant_unique"]}

        # Params specific to the type of change
        if model_name == ChangeActeurUpdateParentId.name():
            model_params["data"] = {"parent_id": row["parent_id"]}
        elif model_name in [
            ChangeActeurCreateAsParent.name(),
            ChangeActeurKeepAsParent.name(),
        ]:
            model_params["data"] = row[COL_PARENT_DATA_NEW]
        elif model_name == ChangeActeurVerifyRevision.name():
            pass  # no additional param, we just check presence
        elif model_name == ChangeActeurDeleteAsParent.name():
            pass  # no additional param, we just delete using id
        else:
            raise ValueError(f"Unexpected model_name: {model_name}")

        # Serialization
        if "data" in model_params:
            model_params["data"] = data_serialize(RevisionActeur, model_params["data"])

        # Validation
        row[COL_CHANGE_MODEL_PARAMS] = model_params
        try:
            change = {
                "order": row[COL_CHANGE_ORDER],
                "reason": row[COL_CHANGE_REASON],
                "model_name": row[COL_CHANGE_MODEL_NAME],
                "model_params": row[COL_CHANGE_MODEL_PARAMS],
            }
            SuggestionChange(**change)
        except Exception as e:
            log.preview("🔴 Broken change", change)
            raise e

        # Appending
        changes.append(change)
    return changes


def cluster_acteurs_suggestions_prepare(
    df_clusters: pd.DataFrame,
) -> tuple[list[dict], list[dict]]:
    """Generate suggestions from clusters"""
    working = []
    failing = []
    for cluster_id, cluster in df_clusters.groupby("cluster_id"):

        # Business decided they prefer to skip failing clusters
        # but still try to cluster whatever works than bail out
        # whenever we encounter issues
        try:
            changes = cluster_changes_get(cluster)
            title = "📦 Cluster/dédup"
            suggestion = {"title": title, "cluster_id": cluster_id, "changes": changes}
            df_changes = pd.DataFrame(suggestion["changes"])
            log.preview_df_as_markdown(f"Suggestion pour {cluster_id=}", df_changes)
            working.append(suggestion)
        except Exception:
            import traceback

            error = traceback.format_exc()
            failing.append({"cluster_id": cluster_id, "error": error})
            log.preview(f"🔴 Erreur sur {cluster_id=} 🔴", error)

    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logger.info(f"🟢 {len(working)} suggestions réussies")
    logger.info(f"🔴 {len(failing)} suggestions échouées")

    return working, failing
