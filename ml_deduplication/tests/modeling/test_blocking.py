"""Tests for the XGBoost blocking step (`run_blocking`).

Candidate generation now happens inside an existing duckdb connection: the
caller loads the preprocessed entities into `features_minimal`
(`load_df_acteurs_to_duckdb`), then `run_blocking` builds the mutually-exclusive
predicate tables (departement / geo / siren) and merges them into the `pairs`
table. These tests drive that flow and assert on the resulting candidate pairs.
"""

import polars as pl
import pytest

from ml_deduplication.modeling.xgboost.blocking import run_blocking
from ml_deduplication.modeling.xgboost.utils import (
    create_duckdb_con,
    load_df_acteurs_to_duckdb,
)


def _frame(rows: list[dict]) -> pl.DataFrame:
    schema = {
        "identifiant_unique": pl.String,
        "siren": pl.String,
        "code_postal": pl.String,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "source_id": pl.Int64,
        "acteur_type_id": pl.Int64,
        "nom_clean": pl.String,
        "ville_clean": pl.String,
        "siret": pl.String,
        "telephone": pl.String,
        "code_commune_insee": pl.String,
    }
    data = {
        "identifiant_unique": [r["id"] for r in rows],
        "siren": [r["siren"] for r in rows],
        "code_postal": [r["code_postal"] for r in rows],
        "latitude": [r["lat"] for r in rows],
        "longitude": [r["lon"] for r in rows],
        "source_id": [r["source"] for r in rows],
        "acteur_type_id": [r["type"] for r in rows],
        "nom_clean": [r.get("nom", r["id"]) for r in rows],
        "ville_clean": [r.get("ville", "") for r in rows],
        "siret": [r.get("siret", "") for r in rows],
        "telephone": [r.get("tel", "") for r in rows],
        "code_commune_insee": [r.get("insee", "") for r in rows],
    }
    return pl.DataFrame(data, schema=schema, strict=False)


PARIS = {"lat": 48.85, "lon": 2.35}


def _pair_keys(con) -> set[tuple[str, str]]:
    pairs = con.sql("SELECT identifiant_unique_l, identifiant_unique_r FROM pairs").pl()
    return set(zip(pairs["identifiant_unique_l"], pairs["identifiant_unique_r"]))


@pytest.fixture
def con():
    c = create_duckdb_con()
    yield c
    c.close()


class TestBlocking:
    def test_blocks_and_dedups_on_siren_departement_geo(self, con):
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.8501,
                    "lon": 2.3501,
                    "source": 2,
                    "type": 1,
                },
                {
                    "id": "e3",
                    "siren": "2",
                    "code_postal": "13001",
                    "lat": 43.29,
                    "lon": 5.36,
                    "source": 3,
                    "type": 2,
                },
            ]
        )
        load_df_acteurs_to_duckdb(df, con)
        run_blocking(con)
        # e1-e2 is found through all three predicates but deduped to one pair
        assert _pair_keys(con) == {("e1", "e2")}

    def test_same_source_is_excluded(self, con):
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.8501,
                    "lon": 2.3501,
                    "source": 1,
                    "type": 1,
                },
            ]
        )
        load_df_acteurs_to_duckdb(df, con)
        n = run_blocking(con)
        assert n == 0
        assert _pair_keys(con) == set()

    def test_acteur_type_3_and_4_compatible(self, con):
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 3,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.8501,
                    "lon": 2.3501,
                    "source": 2,
                    "type": 4,
                },
            ]
        )
        load_df_acteurs_to_duckdb(df, con)
        run_blocking(con)
        assert _pair_keys(con) == {("e1", "e2")}

    def test_incompatible_acteur_type_excluded(self, con):
        # type 1 vs 2 (neither 3 nor 4) -> not compatible -> excluded
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.8501,
                    "lon": 2.3501,
                    "source": 2,
                    "type": 2,
                },
            ]
        )
        load_df_acteurs_to_duckdb(df, con)
        run_blocking(con)
        assert _pair_keys(con) == set()

    def test_geo_only_pairs_nearby(self, con):
        # e1 & e2 are in different departments but geographically adjacent ->
        # they pair ONLY through the geo predicate. e3 is far from both and in
        # a different department -> excluded.
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.85,
                    "lon": 2.35,
                    "source": 1,
                    "type": 1,
                },
                {
                    "id": "e2",
                    "siren": "2",
                    "code_postal": "77000",
                    "lat": 48.86,
                    "lon": 2.36,
                    "source": 2,
                    "type": 1,
                },
                {
                    "id": "e3",
                    "siren": "3",
                    "code_postal": "13001",
                    "lat": 43.3,
                    "lon": 5.4,
                    "source": 3,
                    "type": 1,
                },
            ]
        )
        load_df_acteurs_to_duckdb(df, con)
        run_blocking(con)
        assert _pair_keys(con) == {("e1", "e2")}

    def test_empty_input_returns_zero(self, con):
        df = _frame([])
        load_df_acteurs_to_duckdb(df, con)
        assert run_blocking(con) == 0

    def test_additional_business_rules_injected(self, con):
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.8501,
                    "lon": 2.3501,
                    "source": 2,
                    "type": 1,
                },
            ]
        )
        load_df_acteurs_to_duckdb(df, con)
        # a contradictory extra rule removes every candidate
        run_blocking(con, additional_business_rules_sql_exprs=["1 = 0"])
        assert _pair_keys(con) == set()

    def test_reusing_same_connection_is_idempotent(self, con):
        # A second pipeline run on the same connection must not collide with
        # pre-existing tables (CREATE OR REPLACE keeps re-runs safe).
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.8501,
                    "lon": 2.3501,
                    "source": 2,
                    "type": 1,
                },
            ]
        )
        load_df_acteurs_to_duckdb(df, con)
        run_blocking(con)
        assert _pair_keys(con) == {("e1", "e2")}
        # run again on the same connection -> still works and same result
        load_df_acteurs_to_duckdb(df, con)
        run_blocking(con)
        assert _pair_keys(con) == {("e1", "e2")}
