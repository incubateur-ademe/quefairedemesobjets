"""Integration tests for the full preprocessing pipeline (`preprocess_entities_df`).

Exercises preprocess -> blocking -> feature generation end-to-end on a small
synthetic entity frame, with a fake embedding model in place of a real
SentenceTransformer.
"""

import numpy as np
import polars as pl

from ml_deduplication.modeling.xgboost.preprocessing import (
    preprocess_entities_df,
    preprocess_entities_df_batched,
)


class FakeEmbedder:
    def encode(self, texts, **kwargs):
        # Deterministic NON-zero vectors: real SentenceTransformer embeddings are
        # never all-zero, and the duckdb cosine path (list_cosine_similarity)
        # handles the zero-vector edge case differently than polars-distance.
        rng = np.random.default_rng(0)
        return rng.normal(size=(len(texts), 1024)).astype(np.float32)


def _frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "identifiant_unique": [r["id"] for r in rows],
            "nom": [r["nom"] for r in rows],
            "nom_commercial": [r.get("nom_com", "x") for r in rows],
            "ville": [r["ville"] for r in rows],
            "adresse": [r["ad"] for r in rows],
            "adresse_complement": [None] * len(rows),
            "latitude": [r["lat"] for r in rows],
            "longitude": [r["lon"] for r in rows],
            "source_id": [r["source"] for r in rows],
            "acteur_type_id": [r["type"] for r in rows],
            "siren": [r["siren"] for r in rows],
            "siret": [r["siret"] for r in rows],
            "telephone": [r["tel"] for r in rows],
            "code_postal": [r["cp"] for r in rows],
            "code_commune_insee": [r["insee"] for r in rows],
            "cluster_id": [r.get("cid") for r in rows],
            "cluster_id_split": [None] * len(rows),
        }
    )


def _duplicate_pair() -> list[dict]:
    return [
        {
            "id": "e1",
            "nom": "Dupont",
            "ville": "Paris",
            "ad": "1 rue A",
            "lat": 48.85,
            "lon": 2.35,
            "source": 1,
            "type": 1,
            "siren": "1",
            "siret": "s1",
            "tel": "t1",
            "cp": "75001",
            "insee": "75056",
            "cid": "c1",
        },
        {
            "id": "e2",
            "nom": "Dupont",
            "ville": "Paris",
            "ad": "1 rue A",
            "lat": 48.8501,
            "lon": 2.3501,
            "source": 2,
            "type": 1,
            "siren": "1",
            "siret": "s1",
            "tel": "t1",
            "cp": "75001",
            "insee": "75056",
            "cid": "c1",
        },
    ]


class TestPreprocessEntitiesDf:
    def test_returns_none_when_no_pairs(self):
        # two entities that share nothing (different source is fine but nothing
        # links them) -> no candidate pairs
        df = _frame(
            [
                {
                    "id": "e1",
                    "nom": "A",
                    "ville": "Paris",
                    "ad": "x",
                    "lat": 48.85,
                    "lon": 2.35,
                    "source": 1,
                    "type": 1,
                    "siren": "1",
                    "siret": "a",
                    "tel": "t",
                    "cp": "75001",
                    "insee": "75056",
                },
                {
                    "id": "e2",
                    "nom": "B",
                    "ville": "Marseille",
                    "ad": "y",
                    "lat": 43.3,
                    "lon": 5.4,
                    "source": 2,
                    "type": 2,
                    "siren": "2",
                    "siret": "b",
                    "tel": "u",
                    "cp": "13001",
                    "insee": "13055",
                },
            ]
        )
        assert preprocess_entities_df(df, FakeEmbedder(), include_label=True) is None

    def test_returns_features_and_label(self):
        df = _frame(_duplicate_pair())
        result = preprocess_entities_df(df, FakeEmbedder(), include_label=True)
        assert isinstance(result, tuple)
        X, y = result
        assert "label" not in X.columns
        assert "label" in y.columns
        # the single candidate pair is a true duplicate
        assert y["label"].to_list() == [True]
        assert "identifiant_unique_l" in X.columns
        assert "identifiant_unique_r" in X.columns

    def test_returns_features_only_when_no_label(self):
        df = _frame(_duplicate_pair())
        X = preprocess_entities_df(df, FakeEmbedder(), include_label=False)
        assert not isinstance(X, tuple)
        assert "label" not in X.columns
        assert X["identifiant_unique_l"].to_list() == ["e1"]


class TestIterFeatureBatches:
    def test_batches_concatenate_to_full_preprocess(self):
        # 8 entities sharing siren/department/geo but with distinct sources
        # cross-pair into 8*7/2 = 28 candidate pairs. A small batch_size forces
        # multiple batches whose concatenation must equal the full pipeline.
        df = _frame(
            [
                {
                    "id": f"e{i}",
                    "nom": "Dupont",
                    "ville": "Paris",
                    "ad": "1 rue A",
                    "lat": 48.85 + 1e-4 * i,
                    "lon": 2.35 + 1e-4 * i,
                    "source": i + 1,
                    "type": 1,
                    "siren": "1",
                    "siret": f"s{i}",
                    "tel": f"t{i}",
                    "cp": "75001",
                    "insee": "75056",
                }
                for i in range(8)
            ]
        )
        X_full = preprocess_entities_df(df, FakeEmbedder(), include_label=False)
        assert X_full is not None
        n_full = len(X_full)

        batches = list(
            preprocess_entities_df_batched(
                df, FakeEmbedder(), include_label=False, batch_size=2
            )
        )
        assert len(batches) > 1
        for batch in batches:
            assert len(batch) <= 2
        X_batched = pl.concat(batches).sort(
            ["identifiant_unique_l", "identifiant_unique_r"]
        )
        assert len(X_batched) == n_full
        X_full_sorted = X_full.sort(["identifiant_unique_l", "identifiant_unique_r"])
        assert X_batched.schema == X_full_sorted.schema
        for col in X_full_sorted.columns:
            if col == "adresse_clean_distance":
                # duckdb (list_cosine_similarity) and polars (polars-distance)
                # legitimately differ by a few ULPs of float32 on the cosine, so
                # compare with a tolerance instead of exact equality.
                assert np.allclose(
                    X_batched[col].to_numpy(),
                    X_full_sorted[col].to_numpy(),
                    rtol=1e-4,
                    atol=1e-6,
                )
            else:
                assert X_batched[col].equals(X_full_sorted[col])

    def test_no_candidate_pairs_yields_no_batches(self):
        # Two entities that share nothing produce no candidate pairs, so the
        # generator yields nothing (the empty-input case itself is rejected by
        # preprocess_features before blocking).
        df = _frame(
            [
                {
                    "id": "e1",
                    "nom": "A",
                    "ville": "Paris",
                    "ad": "x",
                    "lat": 48.85,
                    "lon": 2.35,
                    "source": 1,
                    "type": 1,
                    "siren": "1",
                    "siret": "a",
                    "tel": "t",
                    "cp": "75001",
                    "insee": "75056",
                },
                {
                    "id": "e2",
                    "nom": "B",
                    "ville": "Marseille",
                    "ad": "y",
                    "lat": 43.3,
                    "lon": 5.4,
                    "source": 2,
                    "type": 2,
                    "siren": "2",
                    "siret": "b",
                    "tel": "u",
                    "cp": "13001",
                    "insee": "13055",
                },
            ]
        )
        assert (
            list(
                preprocess_entities_df_batched(df, FakeEmbedder(), include_label=False)
            )
            == []
        )
