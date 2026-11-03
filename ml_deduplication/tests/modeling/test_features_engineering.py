"""Tests for the XGBoost feature engineering step (`generate_features`).

In the refactored duckdb pipeline `generate_features` reads the `features`
entity table and the `pairs` table (both materialized by the blocking step) and
writes the `pairs_features` feature table. These tests set up those
input tables directly inside a duckdb connection and assert on the produced
feature columns.
"""

import numpy as np
import polars as pl
import pytest

from ml_deduplication.modeling.xgboost.features_engineering import generate_features
from ml_deduplication.modeling.xgboost.utils import create_duckdb_con


def _features_frame(nom=None, ville=None, cluster=None) -> pl.DataFrame:
    """A small `features`-shaped frame; defaults exercise matching pairs."""
    return pl.DataFrame(
        {
            "identifiant_unique": ["a", "b", "c", "d"],
            "nom_clean": nom or ["dupont", "dupont", "martin", "martin"],
            "ville_clean": ville or ["paris", "paris", "lyon", "lyon"],
            "siren": ["111", "111", "999", "999"],
            "siret": ["111222", "111222", "333444", "333444"],
            "telephone": ["0102030405", "0102030405", "0699988877", "0699988877"],
            "code_commune_insee": ["75056", "75056", "69123", "69123"],
            "code_postal": ["75001", "75001", "69001", "13002"],
            "acteur_type_id": [1, 1, 2, 2],
            "latitude": [48.85, 48.8501, 45.75, 45.75],
            "longitude": [2.35, 2.3501, 4.85, 4.85],
            "cluster_id": cluster or ["clu1", "clu1", None, None],
            "adresse_clean_vector": [
                [1.0, 0.0],
                [1.0, 0.0],
                [0.0, 1.0],
                [1.0, 0.0],
            ],
        }
    )


@pytest.fixture
def con():
    c = create_duckdb_con()
    yield c
    c.close()


def _load(con, features: pl.DataFrame, pairs: list[tuple[str, str]]):
    con.register("features_in", features)
    con.sql("CREATE OR REPLACE TABLE features AS SELECT * FROM features_in")
    pairs_df = pl.DataFrame(
        {
            "identifiant_unique_l": [left for left, _ in pairs],
            "identifiant_unique_r": [r for _, r in pairs],
        }
    )
    con.register("pairs_in", pairs_df)
    con.sql("CREATE OR REPLACE TABLE pairs AS SELECT * FROM pairs_in")


def _pairs_features(con) -> pl.DataFrame:
    return con.sql("SELECT * FROM pairs_features").pl()


class TestGenerateFeatures:
    def test_computes_similarity_and_match_columns(self, con):
        features = _features_frame()
        _load(con, features, [("a", "b"), ("c", "d")])
        generate_features(con, include_label=True)
        df = _pairs_features(con)
        # identical names / ville -> distance 0
        assert df["nom_clean_dist"].to_list() == [0.0, 0.0]
        assert df["ville_clean_dist"].to_list() == [0.0, 0.0]
        # same siren / siret / telephone -> match
        assert df["siren_match"].to_list() == [True, True]
        assert df["siret_match"].to_list() == [True, True]
        assert df["telephone_match"].to_list() == [True, True]
        # identical commune, identical postal for row 0, different dept digit for row 1
        assert df["code_commune_insee_match"].to_list() == [True, True]
        assert df["code_postal_match"].to_list() == [True, False]
        assert df["departement_match"].to_list() == [True, False]

    def test_label_and_cluster_id(self, con):
        features = _features_frame()
        _load(con, features, [("a", "b"), ("c", "d")])
        generate_features(con, include_label=True)
        df = _pairs_features(con)
        # row 0: same cluster -> label True + cluster_id; row 1: null clusters -> False
        assert df["label"].to_list() == [True, False]
        assert df["cluster_id"].to_list() == ["clu1", None]

    def test_no_label_when_excluded(self, con):
        features = _features_frame()
        _load(con, features, [("a", "b")])
        generate_features(con, include_label=False)
        df = _pairs_features(con)
        assert "label" not in df.columns
        assert "cluster_id" not in df.columns

    def test_adresse_distance_computed_with_embeddings(self, con):
        features = _features_frame()
        _load(con, features, [("a", "b"), ("c", "d")])
        generate_features(con, include_label=False)
        dist = _pairs_features(con)["adresse_clean_distance"].to_list()
        assert dist[0] == pytest.approx(0.0, abs=1e-6)  # a vs b identical
        assert dist[1] == pytest.approx(1.0, abs=1e-6)  # c vs d orthogonal

    def test_null_embedding_gives_null_distance(self, con):
        features = _features_frame().with_columns(
            pl.when(pl.col("identifiant_unique").is_in(["a", "c"]))
            .then(None)
            .otherwise(pl.col("adresse_clean_vector"))
            .alias("adresse_clean_vector")
        )
        _load(con, features, [("a", "b"), ("c", "d")])
        generate_features(con, include_label=False)
        dist = _pairs_features(con)["adresse_clean_distance"].to_list()
        # neither pair has both sides present -> null
        assert all(d is None or np.isnan(d) for d in dist)

    def test_geo_distance_computed(self, con):
        features = _features_frame()
        _load(con, features, [("a", "b")])
        generate_features(con, include_label=False)
        d = _pairs_features(con)["geo_distance"].to_list()
        # a & b are ~ tens of meters apart
        assert d[0] < 1000

    def test_additional_columns_kept_with_l_r_suffixes(self, con):
        features = _features_frame()
        _load(con, features, [("a", "b")])
        generate_features(
            con, include_label=False, additional_columns_to_keep=["siren"]
        )
        df = _pairs_features(con)
        assert "siren_l" in df.columns
        assert "siren_r" in df.columns
