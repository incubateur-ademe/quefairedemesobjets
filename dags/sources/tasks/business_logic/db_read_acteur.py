import logging

import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_read_acteur(
    df_normalized: pd.DataFrame,
):
    if "source_id" not in df_normalized.columns:
        raise ValueError(
            "La colonne source_id est requise dans la dataframe normalisée"
        )
    engine = PostgresConnectionManager().django_engine
    unique_source_ids = df_normalized["source_id"].unique()

    joined_source_ids = ",".join([f"'{source_id}'" for source_id in unique_source_ids])
    query = f"SELECT * FROM qfdmo_acteur WHERE source_id IN ({joined_source_ids})"
    log.preview("Requête SQL pour df_acteur", query)
    df_acteur = pd.read_sql_query(query, engine)
    logger.info(f"Nombre d'acteurs existants: {len(df_acteur)}")
    if df_acteur.empty:
        logger.warning("Aucun acteur trouvé: OK si 1ère fois qu'on ingère la source")
    log.preview("df_acteur retourné par la tâche", df_acteur)
    return df_acteur
