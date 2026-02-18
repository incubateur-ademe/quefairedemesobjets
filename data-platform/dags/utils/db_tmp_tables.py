"""Utilities for managing temporary tables in the database"""

import json
import logging

import pandas as pd
from sqlalchemy import text
from utils.django import DJANGO_WH_CONNECTION_NAME, django_conn_to_sqlalchemy_engine

logger = logging.getLogger(__name__)


def convert_dict_list_columns_to_json(df: pd.DataFrame) -> pd.DataFrame:
    """Convert columns ending with '_codes' containing dict/list to JSON strings."""
    df_copy = df.copy()

    for col in df_copy.columns:
        # Check if column name ends with '_codes'
        if not col.endswith("_codes"):
            continue

        # Convert columns ending with '_codes' to JSON strings
        df_copy[col] = df_copy[col].apply(
            lambda x: (json.dumps(x, default=str) if isinstance(x, (dict, list)) else x)
        )

    return df_copy


def create_temporary_table(
    df: pd.DataFrame,
    table_name: str,
) -> None:
    """Create a temporary table from a DataFrame in the database.

    Args:
        df: DataFrame to save as a temporary table
        table_name: Name of the temporary table to create
        engine: SQLAlchemy engine for database connection
    """

    # Create a SQLAlchemy engine from the Django connection
    engine = django_conn_to_sqlalchemy_engine(using=DJANGO_WH_CONNECTION_NAME)

    # Create temporary tables in the database
    if not df.empty:
        # Convert dict/list columns to JSON before saving
        df_serialized = convert_dict_list_columns_to_json(df)
        df_serialized.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=1000,
        )
        logger.info(f"Table temporaire créée: {table_name} avec {len(df)} lignes")
    else:
        # For empty DataFrames, still need to convert to ensure schema is correct
        df_empty = convert_dict_list_columns_to_json(df.head(0))
        df_empty.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
        )
        logger.info(f"Table temporaire vide créée: {table_name}")


def convert_json_columns_to_dict_list(df: pd.DataFrame) -> pd.DataFrame:
    """Convert JSON string columns ending with '_codes' back to dict/list"""
    df_copy = df.copy()
    for col in df_copy.columns:
        if col.endswith("_codes"):
            # Convert JSON strings to dict/list
            df_copy[col] = df_copy[col].apply(
                lambda x: (
                    json.loads(x)
                    if isinstance(x, str) and x.strip()
                    else (x if isinstance(x, (dict, list)) or x is None else [])
                )
            )
    return df_copy


def read_and_drop_temporary_table(table_name: str) -> pd.DataFrame:
    """
    Read a temporary table from the database and convert JSON columns back to dict/list.
    Drop the temporary table from the database.
    """
    engine = django_conn_to_sqlalchemy_engine(using=DJANGO_WH_CONNECTION_NAME)

    df = (
        pd.read_sql_table(table_name, engine)
        .replace({pd.NA: None})
        .pipe(convert_json_columns_to_dict_list)
    )

    logger.info(f"Table temporaire lue: {table_name} avec {len(df)} lignes")

    with engine.begin() as conn:  # type: ignore
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
    logger.info(f"Table temporaire supprimée: {table_name}")

    return df
