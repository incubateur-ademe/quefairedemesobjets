"""Tests for the XGBoost feature engineering step (`generate_features`).

Converts a pair frame into the feature columns used for training / inference:
string similarity distances, categorical/boolean match flags, the optional
duplicate label, and the address embedding cosine distance.
"""

import numpy as np
import polars as pl
import pytest

from ml_deduplication.modeling.xgboost.features_engineering import (
    generate_features,
)


def _base_pairs() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "identifiant_unique_l": ["a", "c"],
            "identifiant_unique_r": ["b", "d"],
            "nom_clean_l": ["dupont", "martin"],
            "nom_clean_r": ["dupont", "martin"],
            "ville_clean_l": ["paris", "lyon"],
            "ville_clean_r": ["paris", "lyon"],
            "siren_l": ["111", "999"],
            "siren_r": ["111", "999"],
            "siret_l": ["111222", "333444"],
            "siret_r": ["111222", "333444"],
            "telephone_l": ["0102030405", "0699988877"],
            "telephone_r": ["0102030405", "0699988877"],
            "code_commune_insee_l": ["75056", "69123"],
            "code_commune_insee_r": ["75056", "69123"],
            "code_postal_l": ["75001", "69001"],
            "code_postal_r": ["75001", "13002"],
            "geo_distance": [12.5, 3.2],
            "acteur_type_id_l": [1, 2],
            "acteur_type_id_r": [1, 2],
            "cluster_id_l": ["clu1", None],
            "cluster_id_r": ["clu1", None],
        }
    )


class TestGenerateFeatures:
    def test_computes_similarity_and_match_columns(self):
        df = generate_features(_base_pairs(), include_label=True)
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

    def test_label_and_cluster_id(self):
        df = generate_features(_base_pairs(), include_label=True)
        # row 0: same cluster -> label True + cluster_id; row 1: null clusters -> False
        assert df["label"].to_list() == [True, False]
        assert df["cluster_id"].to_list() == ["clu1", None]

    def test_no_label_when_excluded(self):
        df = generate_features(_base_pairs(), include_label=False)
        assert "label" not in df.columns
        assert "cluster_id" not in df.columns

    def test_adresse_distance_null_without_embeddings(self):
        df = generate_features(_base_pairs(), include_label=False)
        assert df["adresse_clean_distance"].dtype == pl.Float32
        assert df["adresse_clean_distance"].null_count() == df.height

    def test_adresse_distance_computed_with_embeddings(self):
        embeddings = pl.DataFrame(
            {
                "identifiant_unique": ["a", "b", "c", "d"],
                "adresse_clean_vector": [
                    [1.0, 0.0],
                    [1.0, 0.0],  # same as a -> cosine dist 0
                    [0.0, 1.0],
                    [1.0, 0.0],  # orthogonal to c -> cosine dist 1
                ],
            }
        )
        df = generate_features(
            _base_pairs(), include_label=False, df_embeddings=embeddings
        )
        dist = df["adresse_clean_distance"].to_list()
        assert dist[0] == pytest.approx(0.0, abs=1e-6)  # a vs b identical
        assert dist[1] == pytest.approx(1.0, abs=1e-6)  # c vs d orthogonal

    def test_missing_embedding_entity_gives_null(self):
        embeddings = pl.DataFrame(
            {
                "identifiant_unique": ["a"],
                "adresse_clean_vector": [[1.0, 0.0]],
            }
        )
        df = generate_features(
            _base_pairs(), include_label=False, df_embeddings=embeddings
        )
        dist = df["adresse_clean_distance"].to_list()
        # neither pair (a,b) nor (c,d) has both sides present -> null
        assert all(d is None or np.isnan(d) for d in dist)

    def test_additional_columns_kept_with_l_r_suffixes(self):
        df = generate_features(
            _base_pairs(), include_label=False, additional_columns_to_keep=["siren"]
        )
        assert "siren_l" in df.columns
        assert "siren_r" in df.columns
