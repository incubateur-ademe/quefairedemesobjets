"""Tests for the ML-deduplication `acteurs_select` business logic.

This task builds the acteurs pool handed to the inference image: it reuses the
clustering DAG's `_cluster_acteurs_read_base` (already tested elsewhere) and is
ML-specific in how it passes `limit_acteurs` through and persists the pool to a
per-run temp table in the warehouse DB.
"""

import pandas as pd
import pytest
from ml_deduplication.config.constants import (
    ACTEURS_TABLE_PREFIX,
    acteurs_table_name,
)
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select import (
    ml_deduplication_acteurs_select,
)


def _config(limit_acteurs: int | None = None) -> MLDeduplicationConfig:
    return MLDeduplicationConfig.model_validate(
        {
            "dry_run": False,
            "include_sources": [],
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
            "mapping_sources": {"ess": 1},
            "mapping_acteur_types": {"ess": 1},
            "fields_all": ["nom", "identifiant_unique", "source_id"],
        }
    )


class TestActeursTableName:

    def test_prefix(self):
        assert acteurs_table_name("ml_run_1").startswith(ACTEURS_TABLE_PREFIX)

    def test_sanitizes_run_id(self):
        assert acteurs_table_name("2026-09-29T10:00:00") == (
            f"{ACTEURS_TABLE_PREFIX}_20260929T100000"
        )

    def test_empty_run_id(self):
        assert acteurs_table_name("") == f"{ACTEURS_TABLE_PREFIX}_"


@pytest.mark.django_db
class TestMLDeduplicationActeursSelect:

    def _patch_read_base(self, monkeypatch, df):
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

    def test_limit_acteurs_is_passed_through(self, monkeypatch):
        captured = self._patch_read_base(
            monkeypatch,
            pd.DataFrame(
                [{"identifiant_unique": "a1", "nom": "Alpha", "source_id": 1}]
            ),
        )
        created = []
        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select"
            ".create_temporary_table",
            lambda df, table_name: created.append((df, table_name)),
        )

        df, table_name = ml_deduplication_acteurs_select(
            config=_config(limit_acteurs=100), run_id="ml_test"
        )

        assert captured["kwargs"]["limit"] == 100
        assert not df.empty
        assert table_name == acteurs_table_name("ml_test")
        # The pool was persisted to the temp table.
        assert created and created[0][1] == table_name

    def test_no_limit_when_none(self, monkeypatch):
        captured = self._patch_read_base(
            monkeypatch,
            pd.DataFrame(
                [{"identifiant_unique": "a1", "nom": "Alpha", "source_id": 1}]
            ),
        )
        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select"
            ".create_temporary_table",
            lambda df, table_name: None,
        )

        ml_deduplication_acteurs_select(
            config=_config(limit_acteurs=None), run_id="ml_test"
        )
        assert captured["kwargs"]["limit"] is None

    def test_empty_selection_returns_empty_table_name(self, monkeypatch):
        self._patch_read_base(monkeypatch, pd.DataFrame())
        created = []
        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_acteurs_select"
            ".create_temporary_table",
            lambda df, table_name: created.append((df, table_name)),
        )

        df, table_name = ml_deduplication_acteurs_select(
            config=_config(), run_id="ml_test"
        )

        assert df.empty
        assert table_name == ""
        # No temp table written when nothing was selected.
        assert created == []
