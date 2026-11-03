import logging
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import polars as pl
from polars.dataframe.frame import DataFrame
from sklearn.metrics import (
    classification_report,
    fbeta_score,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)


# Where duckdb spills to disk during blocking. The default CWD (/app in the
# inference image) is read-only for the non-root runtime user, so we redirect
# the temp storage to a dedicated writable directory (see the Dockerfile).
DUCKDB_TEMP_DIR = Path(os.environ.get("DUCKDB_TEMP_DIR", "/tmp/duckdb"))
# Bound duckdb's in-memory footprint so the (potentially very large) blocking
# joins and the materialized feature table spill to disk instead of competing
# with the rest of the inference process for RAM. Overridable via the env var.
DUCKDB_MEMORY_LIMIT = os.environ.get("DUCKDB_MEMORY_LIMIT", None)


def select_best_threshold(
    y_pred_scores_dev: np.ndarray, y_dev: np.ndarray, min_recall: float = 0.6
) -> tuple[float, dict]:

    best_threshold = 0
    best_precision = 0

    best_fbeta = 0
    best_fbeta_threshold = 0
    y_pred_scores = y_pred_scores_dev[:, 1]
    for threshold in np.arange(0.1, 1, 0.05):
        y_pred_labels = y_pred_scores >= threshold

        precision = precision_score(y_dev, y_pred_labels)
        recall = recall_score(y_dev, y_pred_labels)
        fbeta = fbeta_score(y_dev, y_pred_labels, beta=0.3)

        if (precision > best_precision) and (recall >= min_recall):
            best_threshold = threshold
            best_precision = precision

        if fbeta > best_fbeta:
            best_fbeta = fbeta
            best_fbeta_threshold = threshold

    if best_precision > 0:
        y_pred_labels_at_best_threshold = y_pred_scores >= best_threshold
    else:
        logger.debug(
            "Using fbeta to get threshold as best precision do not reach min recall."
        )
        best_threshold = best_fbeta_threshold
        y_pred_labels_at_best_threshold = y_pred_scores >= best_threshold
    classification_report_at_best_thresold: dict = classification_report(
        y_dev, y_pred_labels_at_best_threshold, output_dict=True
    )  # type: ignore

    return best_threshold, classification_report_at_best_thresold


def create_duckdb_con(
    database_file: Path | str = ":memory:",
    temp_dir: Path | None = DUCKDB_TEMP_DIR,
    memory_limit: str | None = DUCKDB_MEMORY_LIMIT,
) -> duckdb.DuckDBPyConnection:
    config: dict[Any, Any] = {}
    if temp_dir is not None:
        os.makedirs(temp_dir, exist_ok=True)
        config["temp_directory"] = temp_dir
    if memory_limit is not None:
        config["memory_limit"] = memory_limit
    con = duckdb.connect(database=database_file, config=config)
    con.install_extension("spatial")
    con.load_extension("spatial")

    return con


def load_df_acteurs_to_duckdb(
    df_acteurs: pl.DataFrame,
    con: duckdb.DuckDBPyConnection,
    additional_columns_to_keep: list[str] | None = None,
):
    con.register(
        "acteurs",
        df_acteurs.with_columns(
            [
                pl.col("latitude").cast(pl.Float32),
                pl.col("longitude").cast(pl.Float32),
            ]
        ),
    )

    cols_needed = [
        "identifiant_unique",
        "siren",
        "code_postal",
        "latitude",
        "longitude",
        "source_id",
        "acteur_type_id",
    ]
    if additional_columns_to_keep is not None:
        for colname in additional_columns_to_keep:
            if colname not in cols_needed:
                cols_needed.append(colname)

    cols_needed_expr = ",".join(cols_needed)
    con.sql(f"""
    CREATE OR REPLACE TABLE features AS
        SELECT
            *,
            ST_Point2D(longitude,latitude) as location
        FROM acteurs;
    CREATE OR REPLACE TABLE features_minimal AS
        SELECT
            {cols_needed_expr},
            ST_Point2D(longitude,latitude) as location
        FROM acteurs;
    """)


def get_features_df_from_duckdb(
    con: duckdb.DuckDBPyConnection,
) -> pl.DataFrame:
    """Import the whole ``pairs_features`` table as a single polars frame."""
    return con.sql("SELECT * FROM pairs_features").pl()


def get_features_df_batches_from_duckdb(
    con: duckdb.DuckDBPyConnection, batch_size: int
) -> Generator[pl.DataFrame]:
    """Stream the ``pairs_features`` table in Arrow record batches of
    ``batch_size`` rows, converted on the fly to polars frames."""
    reader = con.sql("SELECT * FROM pairs_features").to_arrow_reader(
        batch_size=batch_size
    )
    for batch_arrow in reader:
        df: DataFrame = pl.from_arrow(batch_arrow)  # type: ignore
        yield df
