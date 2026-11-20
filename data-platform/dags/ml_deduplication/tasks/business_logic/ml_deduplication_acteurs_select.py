"""Select the acteurs pool for a run and persist it as a temp table.

The pool (which depends on the selection params) is written to a temporary
table in the warehouse DB. The inference image then reads `SELECT *` from that
table (passed as `--acteurs-table`), so no file transfer is needed. The table
is dropped by the cleanup task at the end of the run.

When `include_sources` restricts which acteurs are candidates, the pool also
carries a `_linkage` column (source_id for the candidate sources, -1 for the
others) handed to the inference as `--linkage-column`, so candidates are only
paired with the other acteurs of the pool.
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
) -> tuple[pd.DataFrame, str, str]:
    """Select acteurs per config and write them to a temp table.

    Returns:
        tuple[pd.DataFrame, str, str]: the selected acteurs, the temp table
        name, and the effective linkage column to pass to the inference
        --linkage-column flag. The linkage column is ``"_linkage"`` when the
        run only considers some sources as candidates (``include_sources``
        set) and ``""`` otherwise (classic deduplication).
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
        return df, "", ""

    # The `_linkage` column drives the cross-dataset linkage rule at inference
    # time: pairs are only kept when the two sides have different values.
    #   - classic mode (no explicit include_sources): no linkage, the column
    #     is a constant 0 placeholder and the DAG does NOT pass --linkage-column
    #   - candidate-source mode: candidate acteurs keep their source_id, all
    #     other acteurs get -1, so pairs are limited to (candidate, any-other).
    df["_linkage"] = 0
    linkage_column = ""
    if config.include_sources:
        # Some parents are not marked as parents and are not filtered,
        # as they have no source_id we filter them.
        df = df.dropna(subset=["source_id"])
        df["source_id"] = df["source_id"].astype(int)

        # The use case for using include source is to only have pairs of candidate with
        # left entities only in selected sources ids
        # but compare them with all other sources.
        # Thus we use the source id as a linkage condition, every sources not being
        # included will have -1 as value that allows them to be paired with all included
        # sources that will keep their original source ids.
        df["_linkage"] = df["source_id"].where(
            cond=df["source_id"].isin(config.include_source_ids), other=-1
        )
        linkage_column = "_linkage"

    table_name = temp_acteurs_table_name(run_id)
    logger.info(log.banner_string("Création de la table temporaire du pool d'acteurs"))
    create_temporary_table(
        df=df,
        table_name=table_name,
    )
    log.preview_df_as_markdown("acteurs sélectionnés", df)

    return df, table_name, linkage_column
