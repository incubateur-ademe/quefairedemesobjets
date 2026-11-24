"""Tests for the OSM dataset cleanup task."""

import logging

import pytest

from osm.tasks.cleanup import osm_dataset_cleanup_task


@pytest.fixture
def logger(monkeypatch):
    # log.logger_get() inspects the call stack and assumes the Airflow
    # runtime depth, so in tests we replace it with a plain logger.
    test_logger = logging.getLogger("test.osm.cleanup")
    monkeypatch.setattr("osm.tasks.cleanup.log.logger_get", lambda: test_logger)


class TestOsmDatasetCleanupTask:
    def test_none_path_does_not_raise(self, logger):
        # Le téléchargement a échoué : aucun fichier n'a été produit.
        osm_dataset_cleanup_task.function(None)

    def test_deletes_parent_directory(self, logger, tmp_path):
        dataset_directory = tmp_path / "osm_dag"
        dataset_directory.mkdir()
        dataset_filepath = dataset_directory / "dataset.osm.pbf"
        dataset_filepath.write_text("data")

        osm_dataset_cleanup_task.function(str(dataset_filepath))

        assert not dataset_directory.exists()

    def test_missing_directory_does_not_raise(self, logger, tmp_path):
        filepath = str(tmp_path / "missing" / "dataset.osm.pbf")
        osm_dataset_cleanup_task.function(filepath)
