import logging

import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_read_acteur(
    df_normalized: pd.DataFrame,
):
    if "source_code" not in df_normalized.columns:
        raise ValueError(
            "La colonne source_codes est requise dans la dataframe normalisée"
        )
    engine = PostgresConnectionManager().engine
    unique_source_codes = df_normalized["source_code"].unique()

    joined_source_codes = ",".join(
        [f"'{source_code}'" for source_code in unique_source_codes]
    )
    query = f"""
    SELECT * FROM qfdmo_acteur
    JOIN qfdmo_source ON qfdmo_acteur.source_id = qfdmo_source.id
    WHERE qfdmo_source.code IN ({joined_source_codes})
    """
    log.preview("Requête SQL pour df_acteur", query)
    df_acteur = pd.read_sql_query(query, engine)
    logger.info(f"Nombre d'acteurs existants: {len(df_acteur)}")
    if df_acteur.empty:
        logger.warning("Aucun acteur trouvé: OK si 1ère fois qu'on ingère la source")
    log.preview("df_acteur retourné par la tâche", df_acteur)
    return df_acteur
