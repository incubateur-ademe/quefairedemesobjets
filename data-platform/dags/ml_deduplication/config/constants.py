"""Constants for the ML-deduplication DAG.

The ML inference image performs the clustering, so unlike the clustering DAG
we do not need clustering/normalization fields. We still reuse the acteur
selection and enrichment constants/business logic from the clustering DAG.
"""

from cluster.config.constants import FIELDS_PARENT_DATA_EXCLUDED, FIELDS_PROTECTED

# Display name of the DAG, reused as `identifiant_action` for the suggestions
# cohorte written to the DB by the `suggestions_to_db` task.
DAG_DISPLAY_NAME = "ML - Deduplication - Inference sur instance on-demand"

# Table (in the warehouse DB) holding the pool of acteurs handed to the
# inference image. It is created per run from the selected acteurs, then
# dropped during cleanup.
ACTEURS_TABLE_PREFIX = "ml_dedup_acteurs"


def acteurs_table_name(run_id: str) -> str:
    """Name of the temp table holding the selected acteurs pool for a run.

    Only letters/digits/underscores are allowed by the inference table-name
    regex, so we sanitize the run_id (already a safe slug in practice).
    """
    safe = "".join(c for c in run_id if c.isalnum() or c in "_")
    return f"{ACTEURS_TABLE_PREFIX}_{safe}"


__all__ = [
    "FIELDS_PARENT_DATA_EXCLUDED",
    "FIELDS_PROTECTED",
    "ACTEURS_TABLE_PREFIX",
    "acteurs_table_name",
]
