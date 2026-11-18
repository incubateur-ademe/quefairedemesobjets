"""Tests for the ML-deduplication `clusters_select` task business logic.

These cover the post-inference enrichment: reading the clusters produced by the
inference, joining the full acteurs, and producing a DataFrame whose shape
matches what the (reused) clustering parent/suggestion tasks expect
(`cluster_id`, `parent_id`, `est_parent`, and the computed `nombre_enfants`
property required by `df_metadata_get`).
"""

import pandas as pd
import pytest
from ml_deduplication.config.models import MLDeduplicationConfig
from ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select import (
    _clusters_read,
    filter_clusters_without_any_included_sources,
    ml_deduplication_clusters_select,
)


def _config(fields_all: list[str] | None = None) -> MLDeduplicationConfig:
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
            "mapping_sources": {"ess": 1},
            "mapping_acteur_types": {"ess": 1},
            "fields_all": fields_all
            or [
                "nom",
                "identifiant_unique",
                "acteur_type_id",
                "source_id",
                "parent_id",
            ],
        }
    )


def _acteurs_df() -> pd.DataFrame:
    """A DataFrame shaped like `_acteurs_read_for_entities` output."""
    return pd.DataFrame(
        [
            {
                "identifiant_unique": "a1",
                "nom": "Alpha",
                "acteur_type_id": 1,
                "source_id": 1,
                "parent_id": None,
                "nombre_enfants": 2,
                "source_code": "ess",
                "acteur_type_code": "ess",
                "source_codes": ["ess"],
            },
            {
                "identifiant_unique": "a2",
                "nom": "Beta",
                "acteur_type_id": 1,
                "source_id": 1,
                "parent_id": None,
                "nombre_enfants": 0,
                "source_code": "ess",
                "acteur_type_code": "ess",
                "source_codes": ["ess"],
            },
        ],
        dtype="object",
    )


@pytest.mark.django_db
class TestMLDeduplicationClustersSelect:

    @pytest.fixture
    def mock_db_seams(self, monkeypatch):
        """Replace the DB-reading helpers so we test the enrichment only."""

        def fake_clusters_read(run_id, output_table):
            return pd.DataFrame(
                [
                    {"entity_id": "a1", "cluster_id": "c1", "score_true": 0.9},
                    {"entity_id": "a2", "cluster_id": "c1", "score_true": 0.8},
                ]
            )

        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select"
            "._clusters_read",
            fake_clusters_read,
        )

        captured = {}

        def fake_acteurs_read_for_entities(entities, fields):
            captured["fields"] = list(fields)
            df = _acteurs_df()
            return df[df["identifiant_unique"].isin(entities)]

        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select"
            "._acteurs_read_for_entities",
            fake_acteurs_read_for_entities,
        )

        # No existing parents -> parent_id stays None.
        monkeypatch.setattr(
            "qfdmo.models.RevisionActeur.objects.filter",
            lambda *a, **k: type(
                "FakeQS",
                (),
                {"values_list": lambda self, *a, **k: []},
            )(),
        )
        return captured

    def test_fields_read_include_nombre_enfants(self, mock_db_seams):
        """The `nombre_enfants` computed prop must be requested from the acteurs,
        otherwise `df_metadata_get` (suggestions_to_db) fails on a missing column.
        """
        ml_deduplication_clusters_select(config=_config(), run_id="ml_test")
        assert "nombre_enfants" in mock_db_seams["fields"]

    def test_output_has_expected_columns(self, mock_db_seams):
        df = ml_deduplication_clusters_select(config=_config(), run_id="ml_test")

        for col in [
            "cluster_id",
            "parent_id",
            "nombre_enfants",
            "source_code",
            "acteur_type_code",
            "source_codes",
            "identifiant_unique",
        ]:
            assert col in df.columns, f"missing column {col}"

    def test_cluster_id_attached_from_inference(self, mock_db_seams):
        df = ml_deduplication_clusters_select(config=_config(), run_id="ml_test")
        assert set(df["cluster_id"]) == {"c1"}
        assert set(df["identifiant_unique"]) == {"a1", "a2"}

    def test_empty_clusters_returns_empty_df(self, monkeypatch):
        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select"
            "._clusters_read",
            lambda run_id, output_table: pd.DataFrame(),
        )
        df = ml_deduplication_clusters_select(config=_config(), run_id="ml_test")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_drops_acteurs_without_cluster(self, monkeypatch):
        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select"
            "._clusters_read",
            lambda run_id, output_table: pd.DataFrame(
                [{"entity_id": "a1", "cluster_id": "c1", "score_true": 0.9}]
            ),
        )
        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select"
            "._acteurs_read_for_entities",
            lambda entities, fields: _acteurs_df(),  # returns a1 AND a2
        )
        monkeypatch.setattr(
            "qfdmo.models.RevisionActeur.objects.filter",
            lambda *a, **k: type(
                "FakeQS", (), {"values_list": lambda self, *a, **k: []}
            )(),
        )
        df = ml_deduplication_clusters_select(config=_config(), run_id="ml_test")
        assert set(df["identifiant_unique"]) == {"a1"}
        assert "a2" not in set(df["identifiant_unique"])


class TestFilterClustersWithoutAnyIncludedSources:

    def test_keeps_clusters_with_an_included_source(self):
        df = pd.DataFrame(
            [
                {"cluster_id": "c1", "source_id": 1},
                {"cluster_id": "c1", "source_id": 2},
                {"cluster_id": "c2", "source_id": 3},
            ]
        )
        out = filter_clusters_without_any_included_sources(df, include_source_ids=[1])
        assert set(out["cluster_id"]) == {"c1"}

    def test_drops_clusters_without_any_included_source(self):
        df = pd.DataFrame(
            [
                {"cluster_id": "c1", "source_id": 3},
                {"cluster_id": "c2", "source_id": 4},
            ]
        )
        out = filter_clusters_without_any_included_sources(df, include_source_ids=[1])
        assert out.empty

    def test_all_sources_keeps_everything(self):
        df = pd.DataFrame(
            [{"cluster_id": "c1", "source_id": 1}, {"cluster_id": "c2", "source_id": 2}]
        )
        out = filter_clusters_without_any_included_sources(
            df, include_source_ids=[1, 2]
        )
        assert set(out["cluster_id"]) == {"c1", "c2"}


class TestClustersRead:

    def test_only_multi_entity_clusters_are_kept(self, monkeypatch):
        engine = object()

        def fake_read_sql(sql, eng, params):
            assert params["run_id"] == "ml_test"
            return pd.DataFrame(
                [
                    {"entity_id": "a1", "cluster_id": "c1", "run_id": "ml_test"},
                    {"entity_id": "a2", "cluster_id": "c1", "run_id": "ml_test"},
                    {"entity_id": "a3", "cluster_id": "c2", "run_id": "ml_test"},
                    {"entity_id": "a4", "cluster_id": "c3", "run_id": "ml_test"},
                    {"entity_id": "a5", "cluster_id": "c3", "run_id": "ml_test"},
                ]
            )

        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select"
            ".django_conn_to_sqlalchemy_engine",
            lambda **kwargs: engine,
        )
        monkeypatch.setattr(
            "ml_deduplication.tasks.business_logic.ml_deduplication_clusters_select"
            ".pd.read_sql",
            fake_read_sql,
        )

        df = _clusters_read(run_id="ml_test", output_table="public.ml_deduplication")
        # c2 has only 1 entity -> dropped; c1 & c3 have 2 -> kept
        assert set(df["cluster_id"]) == {"c1", "c3"}
