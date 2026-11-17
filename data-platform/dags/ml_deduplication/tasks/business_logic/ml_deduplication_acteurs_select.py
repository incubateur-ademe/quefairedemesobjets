"""Select the acteurs pool for a run and persist it as a temp table.

The pool (which depends on the selection params) is written to a temporary
table in the warehouse DB. The inference image then reads `SELECT *` from that
table (passed as `--acteurs-table`), so no file transfer is needed. The table
is dropped by the cleanup task at the end of the run.
"""

import logging

import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_read.for_clustering import (
    _cluster_acteurs_read_base,
)
from ml_deduplication.config.constants import temp_acteurs_table_name
from ml_deduplication.config.models import MLDeduplicationConfig
from utils import logging_utils as log
from utils.db_tmp_tables import create_temporary_table

logger = logging.getLogger(__name__)


def ml_deduplication_acteurs_select(
    config: MLDeduplicationConfig,
    run_id: str,
) -> tuple[pd.DataFrame, str]:
    """Select acteurs per config and write them to a temp table.

    Returns:
        tuple[pd.DataFrame, str]: the selected acteurs and the temp table name.
    """
    df, _ = _cluster_acteurs_read_base(
        fields=config.fields_all,
        include_source_ids=None,
        exclude_source_ids=config.exclude_source_ids,
        include_acteur_type_ids=config.include_acteur_type_ids,
        include_only_if_regex_matches_nom=None,
        include_if_all_fields_filled=None,
        est_parent=False,
        only_active=True,
        limit=config.limit_acteurs,
        dtype=None,
    )

    if df.empty:
        logger.info("Aucun acteur sélectionné, on s'arrête là")
        return df, ""

    df["_linkage"] = True
    if (
        config.include_acteur_type_ids is not None
        and len(config.include_acteur_type_ids) > 0
    ):
        # The use case for using include source is to only have pairs of candidate with
        # left entities only in selected sources ids
        # but compare them with all other sources
        linkage_column_expr = df["source_id"].isin(config.include_acteur_type_ids)
        df["_linkage"] = linkage_column_expr

    table_name = temp_acteurs_table_name(run_id)
    logger.info(log.banner_string("Création de la table temporaire du pool d'acteurs"))
    create_temporary_table(
        df=df,
        table_name=table_name,
    )
    log.preview_df_as_markdown("acteurs sélectionnés", df)

    return df, table_name
