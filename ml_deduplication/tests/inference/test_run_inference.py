"""Tests for the xgboost inference linkage rule (`linkage_rule`).

The DAG feeds a `_linkage` column (numeric: source ids + a `-1` catch-all) to
the inference. The rule must keep only cross-dataset pairs and work with both
string and numeric ids: a numeric column used to trip duckdb's
``coalesce(int, '')`` ConversionException before it was fixed.
"""

import polars as pl
import pytest

from ml_deduplication.inference.xgboost.run_inference import linkage_rule
from ml_deduplication.modeling.xgboost.blocking import run_blocking
from ml_deduplication.modeling.xgboost.utils import (
    create_duckdb_con,
    load_df_acteurs_to_duckdb,
)


class TestLinkageRule:
    def test_returns_rule_and_column_to_keep(self):
        rules, columns = linkage_rule("_linkage")

        assert columns == ["_linkage"]
        assert len(rules) == 1
        # Both sides are compared for difference, so pairs with equal values
        # are dropped at blocking time.
        assert "_linkage_l" in rules[0]
        assert "_linkage_r" in rules[0]
        assert "<>" in rules[0]

    def test_rule_casts_to_varchar(self):
        # The cast keeps the rule valid for numeric columns too (duckdb would
        # otherwise fail on `coalesce(int, '')`).
        (rule,) = linkage_rule("_linkage")[0]
        assert "cast(_linkage_l as varchar)" in rule.lower()
        assert "cast(_linkage_r as varchar)" in rule.lower()


def _frame(rows: list[dict]) -> pl.DataFrame:
    schema = {
        "identifiant_unique": pl.String,
        "siren": pl.String,
        "code_postal": pl.String,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "source_id": pl.Int64,
        "acteur_type_id": pl.Int64,
    }
    data = {
        "identifiant_unique": [r["id"] for r in rows],
        "siren": [r["siren"] for r in rows],
        "code_postal": [r["code_postal"] for r in rows],
        "latitude": [r["lat"] for r in rows],
        "longitude": [r["lon"] for r in rows],
        "source_id": [r["source"] for r in rows],
        "acteur_type_id": [r["type"] for r in rows],
    }
    df = pl.DataFrame(data, schema=schema, strict=False)
    if "linkage" in rows[0]:
        df = df.with_columns(
            pl.Series("_linkage", [r["linkage"] for r in rows], strict=False)
        )
    return df


PARIS = {"lat": 48.85, "lon": 2.35}


def _pair_keys(con) -> set[tuple[str, str]]:
    pairs = con.sql("SELECT identifiant_unique_l, identifiant_unique_r FROM pairs").pl()
    return set(zip(pairs["identifiant_unique_l"], pairs["identifiant_unique_r"]))


@pytest.fixture
def con():
    c = create_duckdb_con()
    yield c
    c.close()


def _run_blocking_with_linkage(con, df, linkage_dtype):
    load_df_acteurs_to_duckdb(
        df.with_columns(pl.col("_linkage").cast(linkage_dtype)),
        con,
        additional_columns_to_keep=["_linkage"],
    )
    business_rule, _ = linkage_rule("_linkage")
    return run_blocking(con, additional_business_rules_sql_exprs=business_rule)


class TestLinkageBlocking:
    def test_numeric_linkage_keeps_only_cross_dataset_pairs(self, con):
        # e1/e4 belong to the candidate source (252), e2/e3 are other sources.
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 252,
                    "type": 1,
                    "linkage": 252,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                    "linkage": -1,
                },
                {
                    "id": "e3",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 2,
                    "type": 1,
                    "linkage": -1,
                },
                {
                    "id": "e4",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 252,
                    "type": 1,
                    "linkage": 252,
                },
            ]
        )
        _run_blocking_with_linkage(con, df, pl.Int64)

        # candidate-source acteurs pair with every other source; pairs between
        # two non-candidate (-1) acteurs are dropped — and same-source pairs
        # were already excluded by the base source_id rule.
        assert _pair_keys(con) == {
            ("e1", "e2"),
            ("e1", "e3"),
            ("e2", "e4"),
            ("e3", "e4"),
        }

    def test_numeric_linkage_all_constant_drops_everything(self, con):
        # A constant linkage value (e.g. no include_sources) + forced linkage
        # mode must not crash and simply yields no candidate.
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                    "linkage": 0,
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 2,
                    "type": 1,
                    "linkage": 0,
                },
            ]
        )
        n = _run_blocking_with_linkage(con, df, pl.Int64)
        assert n == 0
        assert _pair_keys(con) == set()

    def test_string_linkage_keeps_only_cross_dataset_pairs(self, con):
        # Documented 'A'/'B' use case: only pairs between different datasets.
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                    "linkage": "A",
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 2,
                    "type": 1,
                    "linkage": "A",
                },
                {
                    "id": "e3",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 3,
                    "type": 1,
                    "linkage": "B",
                },
            ]
        )
        _run_blocking_with_linkage(con, df, pl.String)

        assert _pair_keys(con) == {("e1", "e3"), ("e2", "e3")}
