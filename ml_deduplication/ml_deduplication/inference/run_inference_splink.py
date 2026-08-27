"""Inference script for the ml_deduplication project.

Loads a saved dedupe model, queries acteurs from qfdmo_vueacteur,
builds features, runs clustering, and outputs results.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
from ml_deduplication.modeling.splink_model import (
    BusinessRulesSplink,
    create_ducbdb_backend,
)
from sentence_transformers import SentenceTransformer

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

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

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

    df_acteurs = df_acteurs.rename({"identifiant_unique": "entity_id"}).with_columns(
        pl.lit(None).alias("cluster_id_true"), pl.lit(None).alias("split")
    )
    # Step 2: Load the saved model
    model_path: Path = args.model_path
    embedding_model = SentenceTransformer("Lajavaness/sentence-camembert-large")
    model = BusinessRulesSplink(
        json.load(model_path.open()),
        embedding_model,
        df_features=df_acteurs,
        db_api=create_ducbdb_backend(Path("/Volumes/PRO-G40")),
        unique_fields=(
            "source_id",
            "parent_id",
        ),  # Should not have two parent ids in the same cluster
    )

    # Step 3 : predict
    df_predictions, df_clusters = model.predict(
        threshold=args.model_threshold, build_waterfall_chart=False
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
    df_clusters.write_parquet(args.output_dir / f"inference_clusters_{run_id}.parquet")
    df_predictions.write_parquet(
        args.output_dir / f"inference_predictions_{run_id}.parquet"
    )

    logger.info("Inference complete!")
    logger.info("Parquet output: %s", args.output_dir)
    logger.info("Database run_id: %s", run_id)


if __name__ == "__main__":
    main()
