#!/usr/bin/env bash
#
# Run the `compute_sample_acteur` DAG and wait for it to finish.
#
# `airflow dags test` executes the tasks in-process: it needs neither the
# scheduler loop nor an unpaused DAG, and exits non-zero when a task fails.
#
# This DAG is the only source of the `webapp_sample` database:
#   dbt run/test +tag:sample            warehouse: sample models (+ upstream)
#   copy_db_schema / copy_db_data       webapp    -> webapp_sample (reference tables)
#   copy_displayed_data_from_warehouse  warehouse -> webapp_sample (sampled acteurs)
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose exec -T airflow-scheduler airflow dags test compute_sample_acteur
