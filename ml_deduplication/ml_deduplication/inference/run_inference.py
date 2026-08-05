"""Inference script for the ml_deduplication project.

Loads a saved dedupe model, queries acteurs from qfdmo_vueacteur,
builds features, runs clustering, and outputs results.
"""

import argparse
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
import psycopg
from ml_deduplication.dataset.features_engineering import preprocess_features_dataset
from ml_deduplication.modeling.model import BusinessRulesStaticDedupe
from ml_deduplication.training.features import FEATURES_NAMES_FROM_DATASET
from ml_deduplication.training.utils import (
    generate_pred_pairs_df,
    partition_to_dict,
    partition_to_results_dict,
)
from tqdm import tqdm
from tqdm.contrib.logging import tqdm_logging_redirect

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(message)s", level=logging.DEBUG, force=True
)
logger = logging.getLogger(__name__)


SCRIPT_DIR = Path(__file__).parent.parent.parent
DEFAULT_MODEL_PATH = SCRIPT_DIR / "logs" / "model_tuning_2026_07_28_1214.json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "outputs"


def load_model(model_path: Path) -> BusinessRulesStaticDedupe:
    """Load a saved model from a JSON file."""
    logger.info("Loading model from %s", model_path)
    deduper = BusinessRulesStaticDedupe(settings_file=model_path, num_cores=1)
    deduper._unique_fields = tuple(list(deduper._unique_fields) + ["parent_id"])
    logger.info("Model loaded successfully")
    return deduper


def query_acteurs(database_uri: str) -> pl.DataFrame:
    """Query all acteurs with acteur_type_id IN (4, 3) from qfdmo_vueacteur."""
    sql = """
SELECT * FROM luis.acteurs_inference
    """
    logger.info("Querying acteurs from qfdmo_vueacteur (type 4 or 3)")
    df = pl.read_database_uri(sql, uri=database_uri)
    logger.info("Found %d acteurs", len(df))
    return df


def build_entities_dict(
    df_features: pl.DataFrame, features_names: list[str]
) -> dict[str, dict[str, Any]]:
    """
    Construit un dictionnaire {id_entité: {feature: valeur, ...}} unique
    à partir des colonnes _i / _j de chaque paire.
    """
    entities = {}
    for row in df_features.iter_rows(named=True):
        eid = row["identifiant_unique"]
        if eid not in entities:
            entity = {}
            for feature_name in features_names:
                value = row[feature_name]
                if isinstance(value, (int, float)):
                    value = str(value)
                entity[feature_name] = value

            entity["location"] = (
                row["latitude"],
                row["longitude"],
            )
            entities[eid] = entity

    return entities


def run_inference(
    deduper: BusinessRulesStaticDedupe,
    entities_dict: dict[str, dict[str, Any]],
    threshold: float = 0.85,
) -> list[tuple]:
    """Run clustering on the entities dict and return results."""
    logger.info("Running inference on %d entities", len(entities_dict))
    partition = deduper.partition(entities_dict, threshold)
    logger.info("Clustering complete: %d clusters found", len(partition))
    return list(partition)


def save_clusters_to_db(
    results: dict[str, Any], database_uri: str, run_id: str
) -> None:
    """Save cluster assignments to the database."""
    logger.info("Saving clusters to database")

    with psycopg.connect(database_uri) as conn, conn.cursor() as cur:
        # Create table if it doesn't exist
        cur.execute("""
                CREATE TABLE IF NOT EXISTS luis.deduplication_clusters (
                    run_id TEXT NOT NULL,
                    cluster_id TEXT NOT NULL,
                    acteur_id TEXT PRIMARY KEY,
                    score FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()

        # Upsert clusters
        for cluster_label, acteurs in results.items():
            for acteur in acteurs:
                cur.execute(
                    """
                        INSERT INTO luis.deduplication_clusters (run_id, cluster_id, acteur_id, score)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (acteur_id)
                        DO UPDATE SET
                            cluster_id = EXCLUDED.cluster_id,
                            score = EXCLUDED.score,
                            run_id = EXCLUDED.run_id,
                            created_at = NOW()
                    """,
                    (
                        run_id,
                        cluster_label,
                        acteur["acteur_id"],
                        acteur["score"],
                    ),
                )
        conn.commit()

    logger.info("Clusters saved to database for run %s", run_id)


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

    # Step 1: Load the saved model
    deduper = load_model(args.model_path)

    # Step 2: Query acteurs from database
    df_acteurs = query_acteurs(args.database_uri)
    if len(df_acteurs) == 0:
        logger.warning("No acteurs found with type 4 or 3. Exiting.")
        raise SystemExit(0)

    df_acteurs_preprocessed = preprocess_features_dataset(df_acteurs)

    total_code_postal = df_acteurs_preprocessed.select(
        pl.col("code_postal").n_unique()
    ).item()
    complete_partition = []

    with tqdm_logging_redirect():
        for code_postal, sub_df in tqdm(
            df_acteurs_preprocessed.group_by(
                pl.col("code_postal").str.slice(0, 2),
            ),
            total=total_code_postal,
            colour="BLUE",
        ):
            logger.info("Starting partition for code postal: %s", code_postal[0])
            if len(sub_df) < 2:
                logger.warning("Skipping %s as there is no enough entities.")
                continue

            # Step 3: Build entities dict
            entities_dict = build_entities_dict(
                sub_df, FEATURES_NAMES_FROM_DATASET + ["parent_id"]
            )
            logger.info("Built entities dict with %d entities", len(entities_dict))

            # Step 4: Run inference/clustering
            partition = run_inference(deduper, entities_dict, args.model_threshold)
            complete_partition.extend(partition)
    # Step 5: Convert to results format
    results = partition_to_dict(complete_partition)

    # Count cluster sizes
    cluster_sizes = {}
    for cluster_id in results.values():
        cid = cluster_id
        cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1
    multi_clusters = {k: v for k, v in cluster_sizes.items() if v > 1}
    logger.info(
        "Results: %d entities in %d clusters (%d multi-entity clusters)",
        len(results),
        len(cluster_sizes),
        len(multi_clusters),
    )

    result_df = generate_pred_pairs_df(complete_partition)
    result_dict = partition_to_results_dict(complete_partition)

    # Step 7: Save outputs
    result_df.write_parquet(args.output_dir / f"inference_clusters_{run_id}.parquet")
    save_clusters_to_db(result_dict, args.database_uri, run_id)

    logger.info("Inference complete!")
    logger.info("Parquet output: %s", args.output_dir)
    logger.info("Database run_id: %s", run_id)


if __name__ == "__main__":
    main()
