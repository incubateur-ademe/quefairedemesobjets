"""Tests for the XGBoost blocking step (`block_df`).

Candidate generation happens in duckdb with three predicates (siren, first-two
code_postal digits, 30km geo distance) combined with the business rules
(acteur type compatibility and distinct source). Tests use small synthetic
frames and assert on the resulting candidate pairs.
"""

import polars as pl

from ml_deduplication.modeling.xgboost.blocking import block_df, block_df_batches


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


def _pair_keys(out: pl.DataFrame) -> set[tuple[str, str]]:
    return set(zip(out["identifiant_unique_l"], out["identifiant_unique_r"]))


class TestBlocking:
    def test_blocks_and_dedups_on_siren_departement_geo(self):
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
        out = block_df(df)
        # e1-e2 found through all three predicates but deduped to one pair
        assert _pair_keys(out) == {("e1", "e2")}
        # e3 is far away and shares nothing -> excluded
        row = out.to_pandas().iloc[0]
        assert row["identifiant_unique_l"] == "e1"
        assert row["identifiant_unique_r"] == "e2"
        assert row["geo_distance"] < 1000

    def test_same_source_is_excluded(self):
        # same siren but same source -> the source rule rejects the pair
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
        out = block_df(df)
        assert out.is_empty()

    def test_acteur_type_3_and_4_compatible(self):
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
        out = block_df(df)
        assert _pair_keys(out) == {("e1", "e2")}

    def test_incompatible_acteur_type_excluded(self):
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
        out = block_df(df)
        assert out.is_empty()

    def test_geo_only_pairs_nearby(self):
        # e1 & e2 are in different departments but geographically adjacent ->
        # they pair ONLY through the 30km geo predicate. e3 is far from both
        # and in a different department -> excluded.
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
        out = block_df(df)
        assert _pair_keys(out) == {("e1", "e2")}

    def test_empty_input_returns_empty(self):
        df = _frame([])
        out = block_df(df)
        assert out.is_empty()
        assert {"identifiant_unique_l", "identifiant_unique_r", "geo_distance"} <= set(
            out.columns
        )

    def test_additional_business_rules_injected(self):
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
        # a contradictory extra rule removes every candidate
        out = block_df(df, additional_business_rules_sql_exprs=["1 = 0"])
        assert out.is_empty()

    def test_additional_columns_to_keep(self):
        df = _frame(
            [
                {
                    "id": "e1",
                    "siren": "1",
                    "code_postal": "75001",
                    **PARIS,
                    "source": 1,
                    "type": 1,
                    "ville": "paris",
                },
                {
                    "id": "e2",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.8501,
                    "lon": 2.3501,
                    "source": 2,
                    "type": 1,
                    "ville": "paris",
                },
            ]
        )
        out = block_df(df, additional_columns_to_keep=["ville_clean"])
        assert "ville_clean_l" in out.columns
        assert "ville_clean_r" in out.columns


class TestBlockDfBatches:
    def test_batches_concatenate_to_block_df(self):
        # 4 entities with the same siren, department and geo location generate
        # 4*3/2 = 6 candidate pairs. A batch_size of 2 must split them into
        # several ordered batches whose concatenation equals block_df's output.
        df = _frame(
            [
                {
                    "id": f"e{i}",
                    "siren": "1",
                    "code_postal": "75001",
                    "lat": 48.85 + 1e-4 * i,
                    "lon": 2.35 + 1e-4 * i,
                    "source": i + 1,
                    "type": 1,
                }
                for i in range(4)
            ]
        )
        out_full = block_df(df).sort(["identifiant_unique_l", "identifiant_unique_r"])
        batches = list(block_df_batches(df, batch_size=2))
        assert len(batches) > 1
        for batch in batches:
            assert len(batch) <= 2
        out_batched = pl.concat(batches).sort(
            ["identifiant_unique_l", "identifiant_unique_r"]
        )
        assert out_full.columns == out_batched.columns
        assert out_full.equals(out_batched)

    def test_empty_input_yields_no_batches(self):
        df = _frame([])
        assert list(block_df_batches(df, batch_size=2)) == []
