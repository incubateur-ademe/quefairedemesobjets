"""Cleanup task: drop the temp acteurs pool table."""

import logging

from ml_deduplication.config.constants import acteurs_table_name
from utils.db_tmp_tables import drop_temporary_table

logger = logging.getLogger(__name__)


def ml_deduplication_cleanup(run_id: str | None) -> None:
    """Drop the temp acteurs pool table for the run, if a run_id is known.

    `DROP TABLE IF EXISTS` is idempotent, so it's safe to call even when the
    selection task didn't create the table (e.g. run failed early).
    """
    if not run_id:
        logger.info("Pas de run_id -> rien à nettoyer")
        return
    table_name = acteurs_table_name(run_id)
    drop_temporary_table(table_name)
    logger.info(f"Table temporaire d'acteurs supprimée: {table_name}")
