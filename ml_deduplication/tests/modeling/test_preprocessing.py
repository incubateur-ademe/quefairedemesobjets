"""Tests for the XGBoost preprocessing step.

`strip_ville_from_name` and `preprocess_features` are covered here. The
embedding model is replaced by a lightweight fake so the tests do not load a
real SentenceTransformer.
"""

import numpy as np
import polars as pl

from ml_deduplication.modeling.xgboost.preprocessing import (
    preprocess_features,
    strip_ville_from_name,
)


class FakeEmbedder:
    def __init__(self, dim: int = 1024):
        self.dim = dim

    def encode(self, texts, **kwargs):
        return np.zeros((len(texts), self.dim), dtype=np.float32)


def _entity_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "identifiant_unique": ["a", "b"],
            "nom": ["Dupont", "Martin St-Pierre"],
            "nom_commercial": [None, "Cabane"],
            "ville": [" Paris ", "Saint-Etienne"],
            "adresse": [" 1 rue Test ", None],
            "adresse_complement": ["Bât A", None],
            "latitude": [48.85, 999.0],
            "longitude": [2.35, -999.0],
            "source_id": [1, 2],
            "acteur_type_id": [1, 2],
        }
    )


class TestStripVilleFromName:
    def test_returns_nom_when_ville_empty(self):
        assert (
            strip_ville_from_name(
                {"nom": "Super coiffeur", "ville": "", "ville_clean": ""}
            )
            == "Super coiffeur"
        )

    def test_returns_nom_when_ville_none(self):
        assert (
            strip_ville_from_name(
                {"nom": "Super coiffeur", "ville": None, "ville_clean": None}
            )
            == "Super coiffeur"
        )

    def test_removes_ville_from_nom(self):
        # "saint etienne" is removed from the concatenated name
        assert (
            strip_ville_from_name(
                {
                    "nom": "Au chant saint etienne",
                    "ville": "saint-etienne",
                    "ville_clean": "saint etienne",
                }
            )
            == "Au chant "
        )

    def test_uses_ville_clean_when_available(self):
        # ville_clean has the hyphen replaced by a space, so both variants are
        # removed from the name
        assert (
            strip_ville_from_name(
                {
                    "nom": "Leclaire saint jean de vedas",
                    "ville": "saint-jean-de-vedas",
                    "ville_clean": "saint jean de vedas",
                }
            )
            == "Leclaire "
        )


class TestPreprocessFeatures:
    def test_normalizes_and_cleans_strings(self):
        out = preprocess_features(_entity_frame(), FakeEmbedder())
        row = out.filter(pl.col("identifiant_unique") == "a").to_pandas().iloc[0]
        # lowercase, accent-stripped, whitespace-trimmed (ville is in the
        # lowercased set; adresse is only trimmed)
        assert row["ville"] == "paris"
        # "__empty__"/"" become null; whitespace is trimmed but case is kept
        assert row["adresse"] == "1 rue Test"

    def test_ville_clean_transformations(self):
        out = preprocess_features(_entity_frame(), FakeEmbedder())
        row = out.filter(pl.col("identifiant_unique") == "b").to_pandas().iloc[0]
        # "st" -> "saint", "-" -> " ", lowercase
        assert row["ville_clean"] == "saint etienne"

    def test_nom_clean_concatenates_and_removes_ville(self):
        out = preprocess_features(_entity_frame(), FakeEmbedder())
        row = out.filter(pl.col("identifiant_unique") == "b").to_pandas().iloc[0]
        # nom + nom_commercial = "martin st-pierre cabane", ville "saint etienne" removed
        assert "martin" in row["nom_clean"]
        assert "cabane" in row["nom_clean"]
        assert "saint etienne" not in row["nom_clean"]

    def test_adresse_clean_concatenates(self):
        out = preprocess_features(_entity_frame(), FakeEmbedder())
        row = out.filter(pl.col("identifiant_unique") == "a").to_pandas().iloc[0]
        # adresse/adresse_complement are concatenated but NOT lowercased
        assert row["adresse_clean"] == "1 rue Test Bât A"

    def test_lat_long_clipped(self):
        out = preprocess_features(_entity_frame(), FakeEmbedder())
        row = out.filter(pl.col("identifiant_unique") == "b").to_pandas().iloc[0]
        assert row["latitude"] == 90.0
        assert row["longitude"] == -180.0

    def test_schema_casts_applied(self):
        out = preprocess_features(_entity_frame(), FakeEmbedder())
        assert out.schema["source_id"] == pl.Int16
        assert out.schema["acteur_type_id"] == pl.Int8

    def test_adresse_clean_vector_computed_or_null(self):
        out = preprocess_features(_entity_frame(), FakeEmbedder())
        # entity "a" has an adresse -> vector; entity "b" has none -> null
        a_vec = out.filter(pl.col("identifiant_unique") == "a")["adresse_clean_vector"][
            0
        ]
        assert a_vec is not None
        assert len(a_vec) == 1024
        b_vec = out.filter(pl.col("identifiant_unique") == "b")["adresse_clean_vector"][
            0
        ]
        assert b_vec is None

    def test_uses_provided_embeddings(self):
        embeddings = pl.DataFrame(
            {
                "identifiant_unique": ["a", "b"],
                "adresse_clean_vector": [
                    np.zeros(1024, dtype=np.float32),
                    np.ones(1024, dtype=np.float32),
                ],
            }
        )
        out = preprocess_features(
            _entity_frame(), FakeEmbedder(), df_embeddings=embeddings
        )
        assert out.height == 2
        assert "adresse_clean_vector" in out.columns
