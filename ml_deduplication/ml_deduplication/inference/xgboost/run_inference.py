"""Inference script for the ml_deduplication project.

Loads a saved xgboost model, reads acteurs either from a local file (CSV or
parquet) or from a database table, builds features, runs clustering, and
outputs results.
"""

import argparse
import json
import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from pickle import load

from sentence_transformers import SentenceTransformer  # isort: skip
import polars as pl
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from ml_deduplication.modeling.xgboost.model import (
    DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
    DEFAULT_SHOULD_BE_EQUAL_FIELDS,
    XGBoostBusinessRulesModel,
)
from ml_deduplication.modeling.xgboost.preprocessing import preprocess_entities_df
from ml_deduplication.modeling.xgboost.schema import OPTIMIZED_SCHEMA
from ml_deduplication.training.xgboost.training import apply_calibrator

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(message)s", level=logging.DEBUG, force=True
)
logger = logging.getLogger(__name__)


SCRIPT_DIR = Path(__file__).parent.parent.parent
DEFAULT_MODEL_PATH = SCRIPT_DIR / "logs" / "model_tuning_2026_07_28_1214.json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "outputs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run inference with a saved deduplication model on acteurs from the database."
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=f"Path to the saved model JSON file (default: {DEFAULT_MODEL_PATH})",
    )
    parser.add_argument(
        "--model-threshold",
        type=float,
        help="Threshold to use for inference. Default to the threshold in the model training results.",
    )
    parser.add_argument(
        "--database-uri",
        type=str,
        default=os.environ.get("DATABASE_CONNECTION_URI", ""),
        help="Database connection URI. Defaults to DATABASE_CONNECTION_URI env var.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run identifier for DB tracking (auto-generated if not provided)",
    )
    parser.add_argument(
        "--split-by-departement",
        action="store_true",
        help="Run identifier for DB tracking (auto-generated if not provided)",
    )
    parser.add_argument(
        "--embeddings-filepath",
        type=Path,
        help="Precomputed embeddings file",
    )
    parser.add_argument(
        "--acteurs-table",
        type=str,
        default=None,
        help="Database table/view name to read acteurs from (requires --database-uri). "
        "Exactly one of acteurs_filepath or --acteurs-table must be provided.",
    )
    parser.add_argument(
        "acteurs_filepath",
        nargs="?",
        type=Path,
        default=None,
        help="Path to a CSV or parquet file containing acteur data to infer. "
        "Exactly one of this or --acteurs-table must be provided.",
    )
    parser.add_argument(
        "--linkage-column",
        type=str,
        default=None,
        help="Name of a column holding the dataset id (e.g. '_dataset' with values "
        "'A'/'B') to run entity linkage between two datasets. Only cross-dataset "
        "pairs (A vs B) are considered at the blocking stage. When not set, the "
        "classic deduplication behavior is kept.",
    )
    parser.add_argument(
        "--output-table",
        type=str,
        default=None,
        help="Base name of the database table(s) to upload results to. Clusters go "
        "to <output-table>_clusters and candidate pairs to <output-table>_predictions, "
        "each tagged with run_id. Requires --database-uri. When not set, results are "
        "only written to parquet in --output-dir.",
    )

    return parser.parse_args()


TABLE_NAME_RE = re.compile(r"^[A-Za-z0-9_.]+$")


def load_acteurs(
    filepath: Path | None, table_name: str | None, database_uri: str
) -> pl.DataFrame:
    """Load acteurs from a local file or a database table/view."""
    if filepath is not None:
        if not filepath.exists():
            raise ValueError(f"{filepath} does not exist")

        match filepath.suffix:
            case ".csv":
                return pl.read_csv(
                    filepath,
                    schema_overrides=OPTIMIZED_SCHEMA,
                    infer_schema=False,
                )
            case ".parquet":
                return pl.read_parquet(filepath)
            case _:
                raise ValueError(
                    "acteurs_filepath has to be either a CSV or a parquet file."
                )

    if table_name is not None:
        if not database_uri:
            raise ValueError(
                "Reading from a table requires a database URI. "
                "Use --database-uri or set the DATABASE_CONNECTION_URI env var."
            )
        if not TABLE_NAME_RE.match(table_name):
            raise ValueError(
                f"Invalid table name {table_name!r}. Only letters, digits, dots "
                "and underscores are allowed."
            )
        sql = f"SELECT * FROM {table_name}"
        logger.info("Querying acteurs from table: %s", table_name)
        df = pl.read_database_uri(sql, uri=database_uri)
        logger.info("Found %d acteurs", len(df))
        return df

    raise ValueError(
        "No acteur source provided: pass an acteurs_filepath or use --acteurs-table."
    )


def linkage_rule(column: str) -> tuple[list[str], list[str]]:
    """Build the blocking rule + column for cross-dataset linkage.

    Returns ``(additional_business_rules_sql_exprs, additional_columns_to_keep)``
    that restrict blocking to cross-dataset (A vs B) candidate pairs only.
    """
    business_rule = f"coalesce(l.{column},'') <> coalesce(r.{column},'')"
    return [business_rule], [column]


def save_results_to_db(
    database_uri: str,
    output_table: str,
    run_id: str,
    df_clusters: pl.DataFrame,
    df_predictions: pl.DataFrame,
) -> None:
    """Upload clusters and predictions to the database.

    Clusters are written to ``<output_table>_clusters`` and candidate pairs to
    ``<output_table>_predictions``, each tagged with ``run_id`` to distinguish
    runs. Tables are created if missing and appended to.
    """
    if not database_uri:
        raise ValueError(
            "Writing results to a table requires a database URI. "
            "Use --database-uri or set the DATABASE_CONNECTION_URI env var."
        )
    if not TABLE_NAME_RE.match(output_table):
        raise ValueError(
            f"Invalid output table name {output_table!r}. Only letters, digits, "
            "dots and underscores are allowed."
        )

    from sqlalchemy import create_engine

    engine = create_engine(database_uri)

    clusters_table = f"{output_table}_clusters"
    df_clusters.with_columns(pl.lit(run_id).alias("run_id")).write_database(
        clusters_table, connection=engine, if_table_exists="append"
    )
    logger.info("Wrote %d cluster rows to %s", len(df_clusters), clusters_table)

    preds_table = f"{output_table}_predictions"
    df_predictions.with_columns(pl.lit(run_id).alias("run_id")).write_database(
        preds_table, connection=engine, if_table_exists="append"
    )
    logger.info("Wrote %d prediction rows to %s", len(df_predictions), preds_table)


def main():
    args = parse_args()

    # Validate model path
    if not args.model_path.exists():
        logger.error("Model file not found: %s", args.model_path)
        raise SystemExit(1)

    # Validate that exactly one acteur source is provided
    if (args.acteurs_filepath is None) == (args.acteurs_table is None):
        logger.error(
            "Provide exactly one acteur source: either an acteurs_filepath "
            "or --acteurs-table (not both, not none)."
        )
        raise SystemExit(1)

    split_by_departement = args.split_by_departement

    linkage_columns_to_keep: list[str] = []
    linkage_sql_exprs: list[str] = []
    if args.linkage_column is not None:
        linkage_sql_exprs, linkage_columns_to_keep = linkage_rule(args.linkage_column)

    output_dir: Path = args.output_dir
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate run ID
    run_id = (
        args.run_id
        or f"inference_{datetime.strftime(datetime.now(UTC), '%Y%m%dT%H%M%S')}"
    )

    # Step 1: Load acteurs (from file or database table)
    df_acteurs = load_acteurs(
        args.acteurs_filepath, args.acteurs_table, args.database_uri
    )

    if len(df_acteurs) == 0:
        logger.warning("No acteurs found Exiting.")
        raise SystemExit(0)

    # Step 2: Load the saved model
    model_path: Path = args.model_path

    df_embeddings = None
    if args.embeddings_filepath is not None:
        df_embeddings = pl.read_parquet(args.embeddings_filepath)
    embedding_model = SentenceTransformer("Lajavaness/sentence-camembert-large")

    model = XGBoostBusinessRulesModel.load(
        xgb_model_path=model_path / "model.json",
        threshold=args.model_threshold,
        n_jobs=-1,
    )
    model._should_be_different_fields = tuple(
        [
            *model._should_be_different_fields,
            "parent_id",
        ]
    )
    with (model_path / "calibrator.pkl").open("rb") as f:
        calibrator: LogisticRegression = load(f)

    threshold = None
    if args.model_threshold is not None:
        threshold = args.model_threshold
    else:
        with (model_path / "training_results.json").open("r") as f:
            training_results = json.load(f)
            threshold = training_results["best_threshold"]
    logger.info("This run will use the value %s as threshold", threshold)

    if split_by_departement:
        dfs_predictions = []
        dfs_clusters = []
        with logging_redirect_tqdm():
            for departement, df in tqdm(
                df_acteurs.group_by(pl.col("code_postal").str.slice(0, 2))
            ):
                departement_code: str = departement[0]
                if len(df) < 2:
                    logger.info(
                        "Not enough acteurs in departement %s to clusterize",
                        departement_code,
                    )
                    continue
                logger.info("Starting prediction for departement %s", departement_code)

                X_temp = preprocess_entities_df(
                    df,
                    embedding_model=embedding_model,
                    additional_columns_to_keep=[
                        *DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
                        *DEFAULT_SHOULD_BE_EQUAL_FIELDS,
                        "parent_id",
                        *linkage_columns_to_keep,
                    ],
                    include_label=False,
                    additional_business_rules_sql_exprs=[
                        "coalesce(l.parent_id,-1) <> coalesce(r.parent_id,-2)",
                        *linkage_sql_exprs,
                    ],
                )
                if (X_temp is None) or (len(X_temp) == 0):
                    continue
                # Step 3 : predict
                df_predictions_tmp = model.predict(X_temp)
                df_calibrated_predictions_tmp = apply_calibrator(
                    calibrator, df_predictions_tmp
                )

                _, df_clusters_tmp = model.cluster(
                    df_calibrated_predictions_tmp.with_columns(
                        pl.col("score_true_calibrated").alias("score_true")
                    ),
                    df_entities=df,
                    threshold=threshold,
                )
                if len(df_predictions_tmp) > 0:
                    dfs_predictions.append(df_calibrated_predictions_tmp)
                if len(df_clusters_tmp) > 0:
                    dfs_clusters.append(
                        df_clusters_tmp.with_columns(
                            pl.format(
                                "dep_{}_{}".format(departement_code, "{}"),
                                "cluster_id",
                            ).alias("cluster_id")
                        )
                    )
        df_predictions = pl.concat(dfs_predictions, how="vertical")
        df_clusters = pl.concat(dfs_clusters, how="vertical")
    else:
        X = preprocess_entities_df(
            df_acteurs,
            embedding_model=embedding_model,
            additional_columns_to_keep=[
                *DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
                *DEFAULT_SHOULD_BE_EQUAL_FIELDS,
                "parent_id",
                *linkage_columns_to_keep,
            ],
            include_label=False,
            additional_business_rules_sql_exprs=[
                "coalesce(l.parent_id,'-1') <> coalesce(r.parent_id,'-2')",
                *linkage_sql_exprs,
            ],
            df_embeddings=df_embeddings,
        )
        if (X is None) or (len(X) == 0):
            logger.warning(
                "No candidate pairs found after blocking. Nothing to predict; exiting."
            )
            raise SystemExit(0)
        # Step 3 : predict
        df_predictions = model.predict(X)
        df_calibrated_predictions = apply_calibrator(calibrator, df_predictions)

        _, df_clusters = model.cluster(
            df_calibrated_predictions.with_columns(
                pl.col("score_true_calibrated").alias("score_true")
            ),
            df_entities=df_acteurs,
            threshold=threshold,
        )

    df_clusters_multi = df_clusters.filter(
        pl.col("cluster_id").count().over("cluster_id") > 1
    )
    # Count cluster sizes
    logger.info(
        "Results: %d entities, %d entities belong to multi-entity clusters",
        df_clusters.select(pl.col("entity_id").n_unique()).item(),
        len(df_clusters_multi),
    )

    # Step 7: Save outputs
    df_clusters.write_parquet(output_dir / f"inference_clusters_{run_id}.parquet")
    df_calibrated_predictions.write_parquet(
        output_dir / f"inference_predictions_{run_id}.parquet"
    )

    # Step 8: Upload to database if an output table was requested
    if args.output_table is not None:
        save_results_to_db(
            args.database_uri,
            args.output_table,
            run_id,
            df_clusters,
            df_calibrated_predictions,
        )

    logger.info("Inference complete!")
    logger.info("Parquet output: %s", output_dir)
    logger.info("run_id: %s", run_id)


if __name__ == "__main__":
    main()
