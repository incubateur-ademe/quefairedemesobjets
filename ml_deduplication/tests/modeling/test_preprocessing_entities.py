"""Integration tests for the full preprocessing pipeline (`preprocess_entities_df`).

Exercises preprocess -> blocking -> feature generation end-to-end on a small
synthetic entity frame, with a fake embedding model in place of a real
SentenceTransformer.
"""

import numpy as np
import polars as pl

from ml_deduplication.modeling.xgboost.preprocessing import preprocess_entities_df


class FakeEmbedder:
    def encode(self, texts, **kwargs):
        return np.zeros((len(texts), 1024), dtype=np.float32)


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
