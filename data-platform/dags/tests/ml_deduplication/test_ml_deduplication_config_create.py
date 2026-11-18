"""Tests for the ML-deduplication config creation and run_id generation."""

import pytest
from ml_deduplication.tasks.business_logic.ml_deduplication_config_create import (
    ml_deduplication_config_create,
    ml_deduplication_run_id_generate,
)


class TestRunIdGenerate:

    def test_sanitizes_to_alnum_and_underscore(self):
        # Letters/digits/_ are kept (T is kept since it's alnum); - : # ( ) space
        # are stripped.
        assert ml_deduplication_run_id_generate("2026-09-29T10:00:00") == (
            "ml_20260929T100000"
        )

    def test_strips_invalid_characters(self):
        assert ml_deduplication_run_id_generate("run #1 (dedup)") == "ml_run1dedup"

    def test_keeps_leading_ml_prefix(self):
        assert ml_deduplication_run_id_generate("ml_abc") == "ml_ml_abc"


@pytest.mark.django_db
class TestMLDeduplicationConfigCreate:

    def test_merges_fields_all_into_config(self):
        params = {
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
            "limit_acteurs": 100,
        }
        fields_all = ["nom", "identifiant_unique", "source_id", "parent_id"]
        config = ml_deduplication_config_create(params, "ml_test", fields_all)

        assert config.fields_all == fields_all
        assert config.output_table == "public.ml_deduplication"
        assert config.limit_acteurs == 100

    def test_fields_protected_includes_nombre_enfants(self):
        params = {
            "dry_run": True,
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
            "limit_acteurs": None,
        }
        config = ml_deduplication_config_create(
            params, "ml_test", ["nom", "identifiant_unique", "source_id"]
        )
        assert "nombre_enfants" in config.fields_protected
