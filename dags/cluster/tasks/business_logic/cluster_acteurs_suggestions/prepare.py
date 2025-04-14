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
        COL_CHANGE_ENTITY_TYPE,
        COL_CHANGE_MODEL_NAME,
        COL_CHANGE_MODEL_PARAMS,
        COL_CHANGE_NAMESPACE,
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

    changes = []
    for _, row in cluster.iterrows():
        row = row.to_dict()
        model_name = row[COL_CHANGE_MODEL_NAME]
        # All acteur-related changes have an "identifiant_unique"
        model_params = {"id": row["identifiant_unique"]}
        # Then params data depends on the type of changes
        if model_name == ChangeActeurUpdateParentId.name():
            model_params["data"] = {"parent_id": row["parent_id"]}
        elif model_name in [
            ChangeActeurCreateAsParent.name(),
            ChangeActeurKeepAsParent.name(),
        ]:
            model_params["data"] = row[COL_PARENT_DATA_NEW]
        elif model_name == ChangeActeurVerifyRevision.name():
            # no extra params to pass for this one
            pass
        elif model_name == ChangeActeurDeleteAsParent.name():
            # to delete parents we already have their id
            pass
        else:
            raise ValueError(f"Unexpected model_name: {model_name}")

        # Serialization
        if "data" in model_params:
            model_params["data"] = data_serialize(RevisionActeur, model_params["data"])

        # Validation
        row[COL_CHANGE_MODEL_PARAMS] = model_params
        change = {
            x.replace(COL_CHANGE_NAMESPACE, ""): row[x]
            for x in [
                COL_CHANGE_ORDER,
                COL_CHANGE_REASON,
                COL_CHANGE_ENTITY_TYPE,
                COL_CHANGE_MODEL_NAME,
                COL_CHANGE_MODEL_PARAMS,
            ]
        }
        try:
            SuggestionChange(**change)
        except Exception as e:
            log.preview("🔴 Broken change", change)
            raise e
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
            suggestion = {"cluster_id": cluster_id, "changes": changes}
            cluster_id = suggestion["cluster_id"]
            df_changes = pd.DataFrame(suggestion["changes"])
            log.preview_df_as_markdown(
                f"Suggestion pour cluster_id={cluster_id}", df_changes
            )
            working.append(suggestion)
        except Exception:
            import traceback

            error = traceback.format_exc()
            failing.append({"cluster_id": cluster_id, "error": error})
            log.preview(f"🔴 Erreur sur {cluster_id=} 🔴", error)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logger.info(f"🟢 {len(working)} suggestions réussies")
    logger.info(f"🔴 {len(failing)} suggestions échouées")

    return working, failing
