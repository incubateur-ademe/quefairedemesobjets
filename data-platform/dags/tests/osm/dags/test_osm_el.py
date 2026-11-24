"""Tests for the OSM Extract and Load DAG structure."""

import os

# Le DAG lit os.environ["DB_WAREHOUSE"] au moment de l'import
# (dans osm/tasks/load_dataset_to_db.py), et le job pytest de la CI
# ne définit pas cette variable : on la fournit par défaut avant l'import.
os.environ.setdefault(
    "DB_WAREHOUSE",
    "postgres://user:password@localhost:5432/warehouse",  # pragma: allowlist secret
)

from osm.dags.osm_el import (  # noqa: E402 - l'env doit être posée avant l'import
    DAG_ID,
    osm_extract_load_dag,
)

EXPECTED_TASK_IDS = {
    "osm_extract_load_config_create_task",
    "download_osm_dataset_task",
    "load_dataset_to_db_task",
    "osm_dataset_cleanup_task",
}


class TestOsmExtractLoadDag:
    def test_dag_id(self):
        assert DAG_ID == "osm_extract_load"
        assert osm_extract_load_dag.dag_id == DAG_ID

    def test_schedule(self):
        assert osm_extract_load_dag.schedule == "0 2 1 * *"

    def test_no_catchup(self):
        assert osm_extract_load_dag.catchup is False

    def test_single_active_run(self):
        assert osm_extract_load_dag.max_active_runs == 1

    def test_all_tasks_present(self):
        assert set(osm_extract_load_dag.task_dict) == EXPECTED_TASK_IDS

    def test_config_create_runs_before_download(self):
        config_task = osm_extract_load_dag.get_task(
            "osm_extract_load_config_create_task"
        )
        assert "download_osm_dataset_task" in config_task.downstream_task_ids

    def test_download_feeds_load_and_cleanup(self):
        download_task = osm_extract_load_dag.get_task("download_osm_dataset_task")
        assert "load_dataset_to_db_task" in download_task.downstream_task_ids
        assert "osm_dataset_cleanup_task" in download_task.downstream_task_ids

    def test_cleanup_runs_after_load(self):
        load_task = osm_extract_load_dag.get_task("load_dataset_to_db_task")
        assert "osm_dataset_cleanup_task" in load_task.downstream_task_ids

    def test_cleanup_is_terminal(self):
        # Le cleanup ne doit jamais être en amont du download,
        # sinon on supprimerait le fichier avant son chargement.
        cleanup_task = osm_extract_load_dag.get_task("osm_dataset_cleanup_task")
        assert cleanup_task.downstream_task_ids == set()
        download_task = osm_extract_load_dag.get_task("download_osm_dataset_task")
        assert "osm_dataset_cleanup_task" not in (download_task.upstream_task_ids)

    def test_cleanup_runs_even_if_upstream_fails(self):
        # Le nettoyage doit s'exécuter même si le téléchargement ou le
        # chargement a échoué pour ne pas laisser le dossier temporaire
        # (créé avec delete=False) sur disque.
        cleanup_task = osm_extract_load_dag.get_task("osm_dataset_cleanup_task")
        # Dans Airflow 3, TriggerRule est un StrEnum : la comparaison
        # avec sa valeur littérale tient.
        assert cleanup_task.trigger_rule == "all_done"
