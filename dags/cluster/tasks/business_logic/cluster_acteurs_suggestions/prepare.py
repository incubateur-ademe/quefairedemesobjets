import pandas as pd
from cluster.config.constants import COL_PARENT_DATA_NEW
from cluster.tasks.business_logic.misc.data_serialize_reconstruct import data_serialize
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()


def cluster_acteurs_suggestions_prepare(
    df_clusters: pd.DataFrame,
) -> list[dict]:
    """Generate suggestions from clusters"""

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

    suggestions = []
    for cluster_id, cluster in df_clusters.groupby("cluster_id"):
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
                model_params["data"] = data_serialize(
                    RevisionActeur, model_params["data"]
                )

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
        suggestions.append({"cluster_id": cluster_id, "changes": changes})
    return suggestions
