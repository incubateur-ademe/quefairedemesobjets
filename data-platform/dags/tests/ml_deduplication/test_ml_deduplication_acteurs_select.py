"""Tests for the ML-deduplication `acteurs_select` business logic.

This task builds the acteurs pool handed to the inference image: it reuses the
clustering DAG's `_cluster_acteurs_read_base` (already tested elsewhere) and is
ML-specific in how it passes `limit_acteurs` through, computes the `_linkage`
column (used as `--linkage-column` to restrict pairs when `include_sources` is
set) and persists the pool to a per-run temp table in the warehouse DB.
"""

import pandas as pd
import pytest
from ml_deduplication.config.constants import (
    ACTEURS_TABLE_PREFIX,
    temp_acteurs_table_name,
)
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select import (
    ml_deduplication_acteurs_select,
)


def _patch_read_base(monkeypatch, df):
    captured = {}

    def fake_read_base(**kwargs):
        captured["kwargs"] = kwargs
        return df, "SELECT ..."

    monkeypatch.setattr(
        "ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select"
        "._cluster_acteurs_read_base",
        fake_read_base,
    )
    return captured


def _patch_create_temporary_table(monkeypatch):
    created = []

    monkeypatch.setattr(
        "ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select"
        ".create_temporary_table",
        lambda df, table_name: created.append((df, table_name)),
    )
    return created


def _config(
    limit_acteurs: int | None = None,
    include_sources: list[str] | None = None,
    mapping_sources: dict[str, int] | None = None,
) -> MLDeduplicationConfig:
    return MLDeduplicationConfig.model_validate(
        {
            "dry_run": False,
            "include_sources": include_sources or [],
            "include_acteur_types": ["ess (id=1)"],
            "dedup_enrich_fields": [],
            "dedup_enrich_exclude_sources": [],
            "dedup_enrich_priority_sources": [],
            "dedup_enrich_keep_empty": False,
            "dedup_enrich_keep_parent_data_by_default": True,
            "acteurs_table": None,
            "output_table": "public.ml_deduplication",
            "image_ref": "test:latest",
            "model_threshold": None,
            "linkage_column": None,
            "split_by_departement": False,
            "limit_acteurs": limit_acteurs,
            "mapping_sources": (
                {"ess": 1, "ecopae": 252}
                if mapping_sources is None
                else mapping_sources
            ),
            "mapping_acteur_types": {"ess": 1},
            "fields_all": ["nom", "identifiant_unique", "source_id"],
        }
    )


class TestActeursTableName:
    def test_prefix(self):
        assert temp_acteurs_table_name("ml_run_1").startswith(ACTEURS_TABLE_PREFIX)

    def test_sanitizes_run_id(self):
        assert temp_acteurs_table_name("2026-09-29T10:00:00") == (
            f"{ACTEURS_TABLE_PREFIX}_20260929T100000"
        )

    def test_empty_run_id(self):
        assert temp_acteurs_table_name("") == f"{ACTEURS_TABLE_PREFIX}_"


@pytest.mark.django_db
class TestMLDeduplicationActeursSelect:
    def test_limit_acteurs_is_passed_through(self, monkeypatch):
        captured = _patch_read_base(
            monkeypatch,
            pd.DataFrame(
                [{"identifiant_unique": "a1", "nom": "Alpha", "source_id": 1}]
            ),
        )
        created = _patch_create_temporary_table(monkeypatch)

        df, table_name, linkage_column = ml_deduplication_acteurs_select(
            config=_config(limit_acteurs=100), run_id="ml_test"
        )

        assert captured["kwargs"]["limit"] == 100
        assert not df.empty
        assert table_name == temp_acteurs_table_name("ml_test")
        # The pool was persisted to the temp table.
        assert created and created[0][1] == table_name

    def test_no_limit_when_none(self, monkeypatch):
        captured = _patch_read_base(
            monkeypatch,
            pd.DataFrame(
                [{"identifiant_unique": "a1", "nom": "Alpha", "source_id": 1}]
            ),
        )
        _patch_create_temporary_table(monkeypatch)

        ml_deduplication_acteurs_select(
            config=_config(limit_acteurs=None), run_id="ml_test"
        )
        assert captured["kwargs"]["limit"] is None

    def test_empty_selection_returns_empty_table_name(self, monkeypatch):
        _patch_read_base(monkeypatch, pd.DataFrame())
        created = _patch_create_temporary_table(monkeypatch)

        df, table_name, linkage_column = ml_deduplication_acteurs_select(
            config=_config(), run_id="ml_test"
        )

        assert df.empty
        assert table_name == ""
        assert linkage_column == ""
        # No temp table written when nothing was selected.
        assert created == []


@pytest.mark.django_db
class TestLinkageColumn:
    def test_classic_mode_has_constant_zero_linkage_and_no_column(self, monkeypatch):
        rows = [
            {"identifiant_unique": "a1", "nom": "Alpha", "source_id": 1},
            {"identifiant_unique": "b1", "nom": "Beta", "source_id": 2},
        ]
        _patch_read_base(monkeypatch, pd.DataFrame(rows))
        created = _patch_create_temporary_table(monkeypatch)

        df, _, linkage_column = ml_deduplication_acteurs_select(
            config=_config(), run_id="ml_test"
        )

        # No include_sources -> classic dedup: no --linkage-column is pushed
        # and the placeholder column is constant 0 for every row.
        assert linkage_column == ""
        assert df["_linkage"].tolist() == [0, 0]
        # The constant placeholder column is persisted with the pool.
        assert "_linkage" in created[0][0].columns

    def test_include_sources_marks_candidates_and_others(self, monkeypatch):
        rows = [
            # ecopae (id=252) is an included source -> candidate
            {"identifiant_unique": "e1", "nom": "Eco A", "source_id": 252},
            # another included source keeps its own source_id
            {"identifiant_unique": "e2", "nom": "Eco B", "source_id": 253},
            # other sources get the -1 catch-all
            {"identifiant_unique": "o1", "nom": "Other", "source_id": 1},
        ]
        _patch_read_base(monkeypatch, pd.DataFrame(rows))
        _patch_create_temporary_table(monkeypatch)

        df, _, linkage_column = ml_deduplication_acteurs_select(
            config=_config(
                include_sources=["ecopae (id=252)", "autre (id=253)"],
                mapping_sources={"ess": 1, "ecopae": 252, "autre": 253},
            ),
            run_id="ml_test",
        )

        # acteurs_select pushes "_linkage" so the DAG forwards it to the
        # inference as --linkage-column.
        assert linkage_column == "_linkage"
        # candidate sources keep their id, all the others get -1
        assert df["_linkage"].tolist() == [252, 253, -1]

    def test_null_source_rows_kept_in_classic_mode(self, monkeypatch):
        rows = [
            {"identifiant_unique": "a1", "nom": "Alpha", "source_id": 1},
            # parents not flagged as such have no source_id
            {"identifiant_unique": "p1", "nom": "Parent", "source_id": None},
        ]
        _patch_read_base(monkeypatch, pd.DataFrame(rows))
        _patch_create_temporary_table(monkeypatch)

        df, _, linkage_column = ml_deduplication_acteurs_select(
            config=_config(), run_id="ml_test"
        )

        # classic dedup: rows without source_id stay in the pool
        assert linkage_column == ""
        assert set(df["identifiant_unique"]) == {"a1", "p1"}
        assert df["_linkage"].tolist() == [0, 0]

    def test_null_source_rows_dropped_in_linkage_mode(self, monkeypatch):
        rows = [
            {"identifiant_unique": "e1", "nom": "Eco A", "source_id": 252},
            {"identifiant_unique": "p1", "nom": "Parent", "source_id": None},
        ]
        _patch_read_base(monkeypatch, pd.DataFrame(rows))
        _patch_create_temporary_table(monkeypatch)

        df, _, linkage_column = ml_deduplication_acteurs_select(
            config=_config(
                include_sources=["ecopae (id=252)"],
            ),
            run_id="ml_test",
        )

        # No source_id -> cannot be mapped to a linkage value -> dropped
        assert linkage_column == "_linkage"
        assert set(df["identifiant_unique"]) == {"e1"}
        assert df["_linkage"].tolist() == [252]
