import logging
from pathlib import Path

import polars as pl
from ml_deduplication.modeling.xgboost.model import (
    DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
    DEFAULT_SHOULD_BE_EQUAL_FIELDS,
)
from ml_deduplication.modeling.xgboost.preprocessing import preprocess_entities_df
from ml_deduplication.training.settings import RANDOM_SEED
from ml_deduplication.training.utils import assign_kfolds
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def prepare_folds(
    df_entities: pl.DataFrame,
    embedding_model: SentenceTransformer,
    n_splits: int = 5,
    cache_data_dir: Path | None = None,
) -> list[dict]:
    """
    Preprocess all KFold splits once.

    This is important because hyperparameters only affect XGBoost,
    not embedding/blocking/feature generation.

    Warning:
        This keeps preprocessed data in memory.
        If your dataset is very large, reduce n_splits or cache to disk.
    """

    df_with_folds = assign_kfolds(
        df_entities,
        n_splits=n_splits,
        seed=RANDOM_SEED,
    )

    additional_columns_to_keep = [
        *DEFAULT_SHOULD_BE_DIFFERENT_FIELDS,
        *DEFAULT_SHOULD_BE_EQUAL_FIELDS,
    ]

    folds = []

    for fold in range(n_splits):
        if (
            (cache_data_dir is not None)
            and cache_data_dir.exists()
            and len(list(cache_data_dir.glob(f"*_fold_{fold}.parquet"))) > 0
        ):
            df_train = pl.read_parquet(cache_data_dir / f"df_train_fold_{fold}.parquet")
            X_train = pl.read_parquet(cache_data_dir / f"X_train_fold_{fold}.parquet")
            y_train = pl.read_parquet(cache_data_dir / f"y_train_fold_{fold}.parquet")
            df_dev = pl.read_parquet(cache_data_dir / f"df_dev_fold_{fold}.parquet")
            X_dev = pl.read_parquet(cache_data_dir / f"X_dev_fold_{fold}.parquet")
            y_dev = pl.read_parquet(cache_data_dir / f"y_dev_fold_{fold}.parquet")
        else:
            logger.info("Preprocessing fold %s/%s", fold + 1, n_splits)

            df_train = df_with_folds.filter(pl.col("fold") != fold).drop("fold")
            df_dev = df_with_folds.filter(pl.col("fold") == fold).drop("fold")

            X_train, y_train = preprocess_entities_df(
                df_train,
                embedding_model=embedding_model,
                additional_columns_to_keep=additional_columns_to_keep,
            )

            X_dev, y_dev = preprocess_entities_df(
                df_dev,
                embedding_model=embedding_model,
                additional_columns_to_keep=additional_columns_to_keep,
            )
            if cache_data_dir is not None:
                cache_data_dir.mkdir(exist_ok=True)
                df_train.write_parquet(cache_data_dir / f"df_train_fold_{fold}.parquet")
                X_train.write_parquet(cache_data_dir / f"X_train_fold_{fold}.parquet")
                y_train.write_parquet(cache_data_dir / f"y_train_fold_{fold}.parquet")
                df_dev.write_parquet(cache_data_dir / f"df_dev_fold_{fold}.parquet")
                X_dev.write_parquet(cache_data_dir / f"X_dev_fold_{fold}.parquet")
                y_dev.write_parquet(cache_data_dir / f"y_dev_fold_{fold}.parquet")

        fold_data = {
            "df_entities_train": df_train,
            "X_train": X_train,
            "y_train": y_train,
            "df_entities_dev": df_dev,
            "X_dev": X_dev,
            "y_dev": y_dev,
        }

        folds.append(fold_data)

    return folds
