import logging

import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_read_acteur_task(**kwargs):
    df_normalized = kwargs["ti"].xcom_pull(task_ids="source_data_normalize")

    log.preview("df_normalized", df_normalized)

    return db_read_acteur(
        df_normalized=df_normalized,
    )


def db_read_acteur(
    df_normalized: pd.DataFrame,
):
    if "source_id" not in df_normalized.columns:
        raise ValueError(
            "La colonne source_id est requise dans la dataframe normalisée"
        )
    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()
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
