"""Tests for the XGBoost business-rules model.

Covers the `predict` slim-mode that bounds the resident memory of the frames
accumulated across streaming inference batches by dropping the heavy `*_l` /
`*_r` string columns that clustering does not need.
"""

import polars as pl
import pytest
from xgboost import XGBClassifier

from ml_deduplication.modeling.xgboost.model import XGBoostBusinessRulesModel


def _make_model() -> XGBoostBusinessRulesModel:
    model = XGBoostBusinessRulesModel({})
    return model


def _make_X() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "identifiant_unique_l": ["a", "b"],
            "identifiant_unique_r": ["c", "d"],
            "nom_clean_dist": [0.1, 0.2],
            "adresse_clean_distance": [0.3, None],
            "ville_clean_dist": [0.4, 0.5],
            "siren_match": [True, False],
            "siret_match": [True, False],
            "telephone_match": [False, True],
            "code_commune_insee_match": [True, True],
            "code_postal_match": [True, False],
            "departement_match": [True, False],
            "geo_distance": [1.0, 2.0],
            "acteur_type_id_l": [1, 2],
            "acteur_type_id_r": [1, 3],
            "source_id_l": ["s1", "s2"],
            "source_id_r": ["s1", "s3"],
            "parent_id_l": [None, "p"],
            "parent_id_r": [None, "p"],
            # heavy string columns carried by the feature frame
            "nom_clean_l": ["x", "y"],
            "ville_clean_l": ["z", "w"],
            "siren_l": ["1", "2"],
        }
    )


@pytest.fixture()
def fitted_model() -> XGBoostBusinessRulesModel:
    model = _make_model()
    X = _make_X()
    model._classifier = XGBClassifier(n_estimators=2)
    model._classifier.fit(X.select(model._feature_columns), [0, 1])
    return model


class TestPredict:
    def test_default_keeps_full_frame(self, fitted_model):
        X = _make_X()
        out = fitted_model.predict(X)
        assert "nom_clean_l" in out.columns
        assert "ville_clean_l" in out.columns
        assert "score_true" in out.columns

    def test_slim_drops_heavy_string_columns(self, fitted_model):
        X = _make_X()
        out = fitted_model.predict(X, slim=True)
        assert not any(
            c in out.columns for c in ["nom_clean_l", "ville_clean_l", "siren_l"]
        )

    def test_slim_keeps_clustering_columns(self, fitted_model):
        X = _make_X()
        out = fitted_model.predict(X, slim=True)
        required = [
            "identifiant_unique_l",
            "identifiant_unique_r",
            "score_true",
            *fitted_model._feature_columns,
            # conflict-check fields (source_id differs, acteur_type_id equals)
            "source_id_l",
            "source_id_r",
            "acteur_type_id_l",
            "acteur_type_id_r",
        ]
        assert set(required) <= set(out.columns)

    def test_slim_same_row_count(self, fitted_model):
        X = _make_X()
        assert len(fitted_model.predict(X, slim=True)) == len(X)
