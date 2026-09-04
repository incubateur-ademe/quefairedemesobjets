"""Inference script for the ml_deduplication project.

Loads a saved dedupe model, queries acteurs from qfdmo_vueacteur,
builds features, runs clustering, and outputs results.
"""

import argparse
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from pickle import load

from sentence_transformers import SentenceTransformer  # isort: skip
import polars as pl
from ml_deduplication.modeling.xgboost.model import (
    DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
    DEFAULT_SHOULD_BE_EQUAL_FIELDS,
    XGBoostBusinessRulesModel,
)
from ml_deduplication.modeling.xgboost.preprocessing import preprocess_entities_df
from ml_deduplication.training.xgboost.training import apply_calibrator
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(message)s", level=logging.DEBUG, force=True
)
logger = logging.getLogger(__name__)


SCRIPT_DIR = Path(__file__).parent.parent.parent
DEFAULT_MODEL_PATH = SCRIPT_DIR / "logs" / "model_tuning_2026_07_28_1214.json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "outputs"


def query_acteurs(database_uri: str) -> pl.DataFrame:
    """Query all acteurs with acteur_type_id IN (4, 3) from qfdmo_vueacteur."""
    sql = """
SELECT * FROM luis.acteurs_inference
    """
    logger.info("Querying acteurs from qfdmo_vueacteur (type 4 or 3)")
    df = pl.read_database_uri(sql, uri=database_uri)
    logger.info("Found %d acteurs", len(df))
    return df


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
        help="Threshold to use for inference. Default to 0.85",
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

    return parser.parse_args()


def main():
    args = parse_args()

    # Validate model path
    if not args.model_path.exists():
        logger.error("Model file not found: %s", args.model_path)
        raise SystemExit(1)

    # Validate database URI
    if not args.database_uri:
        logger.error(
            "No database URI provided. Use --database-uri or set DATABASE_CONNECTION_URI env var."
        )
        raise SystemExit(1)

    split_by_departement = args.split_by_departement

    output_dir: Path = args.output_dir
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate run ID
    run_id = (
        args.run_id
        or f"inference_{datetime.strftime(datetime.now(timezone.utc), '%Y%m%dT%H%M%S')}"
    )

    # Step 1: Query acteurs from database
    df_acteurs = query_acteurs(args.database_uri)
    if len(df_acteurs) == 0:
        logger.warning("No acteurs found with type 4 or 3. Exiting.")
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
                    ],
                    include_label=False,
                    additional_business_rules_exprs=[
                        pl.col("parent_id_l") != pl.col("parent_id_r")
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
                    threshold=args.model_threshold,
                )
                if len(df_predictions_tmp) > 0:
                    dfs_predictions.append(df_predictions_tmp)
                if len(df_clusters_tmp) > 0:
                    dfs_clusters.append(
                        df_clusters_tmp.with_columns(
                            pl.format(
                                f"dep_{departement_code}_{{  }}", "cluster_id"
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
            ],
            include_label=False,
            additional_business_rules_exprs=[
                pl.col("parent_id_l") != pl.col("parent_id_r")
            ],
            df_embeddings=df_embeddings,
        )
        # Step 3 : predict
        df_predictions = model.predict(X)
        df_calibrated_predictions = apply_calibrator(calibrator, df_predictions)

        _, df_clusters = model.cluster(
            df_calibrated_predictions.with_columns(
                pl.col("score_true_calibrated").alias("score_true")
            ),
            df_entities=df_acteurs,
            threshold=args.model_threshold,
        )

    df_clusters_multi = df_clusters.filter(
        pl.col("cluster_id").count().over("cluster_id") > 1
    )
    # Count cluster sizes
    logger.info(
        "Results: %d entities in %d multi-entity clusters",
        df_clusters.select(pl.col("entity_id").n_unique()).item(),
        len(df_clusters_multi),
    )

    # Step 7: Save outputs
    df_clusters.write_parquet(output_dir / f"inference_clusters_{run_id}.parquet")
    df_predictions.write_parquet(output_dir / f"inference_predictions_{run_id}.parquet")

    logger.info("Inference complete!")
    logger.info("Parquet output: %s", output_dir)
    logger.info("Database run_id: %s", run_id)


if __name__ == "__main__":
    main()
