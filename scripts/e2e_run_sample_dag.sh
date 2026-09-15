#!/usr/bin/env bash
#
# Trigger the `compute_sample_acteur` DAG through the Airflow CLI and wait
# for it to finish.
#
# This DAG is the only source of the `webapp_sample` database:
#   dbt run/test +tag:sample            warehouse: sample models (+ upstream)
#   copy_db_schema / copy_db_data       webapp    -> webapp_sample (reference tables)
#   copy_displayed_data_from_warehouse  warehouse -> webapp_sample (sampled acteurs)
#
# The sample covers the EPCIs Auray Quiberon Terre Atlantique and Pays de
# Montbéliard Agglomération, plus every digital acteur.
#
# Environment: DAG_TIMEOUT_SECONDS (default 3600).
set -euo pipefail

cd "$(dirname "$0")/.."

DAG_ID="compute_sample_acteur"
RUN_ID="e2e_$(date +%s)"
TIMEOUT_SECONDS="${DAG_TIMEOUT_SECONDS:-3600}"

airflow_cli() { docker compose exec -T airflow-scheduler airflow "$@" 2>/dev/null; }

docker compose --profile airflow ps airflow-scheduler --format '{{.Status}}' \
  | grep -q "Up" || { echo "✗ airflow-scheduler n'est pas démarré" >&2; exit 1; }

# The scheduler never starts runs of a paused DAG, manual triggers included.
# Unpausing also schedules a run for the latest missed interval, which would
# hold the single max_active_runs slot; deleting the existing runs below frees
# it. The DAG is paused again on exit so it does not run daily on the local
# stack.
airflow_cli dags unpause "$DAG_ID" >/dev/null || true
trap 'airflow_cli dags pause "$DAG_ID" >/dev/null 2>&1 || true' EXIT

# The Airflow 3 CLI has no command to delete a DAG run.
echo "→ purge des runs en attente de $DAG_ID"
docker compose exec -T airflow-db psql -U airflow -d airflow -q -c \
  "DELETE FROM task_instance WHERE dag_id = '$DAG_ID';
   DELETE FROM dag_run WHERE dag_id = '$DAG_ID';" >/dev/null 2>&1 || true

echo "→ déclenchement de $DAG_ID (run_id=$RUN_ID)"
airflow_cli dags trigger "$DAG_ID" --run-id "$RUN_ID" >/dev/null

# Read from the metadata database: the CLI output is a wrapped table mixed
# with warnings.
run_state() {
  docker compose exec -T airflow-db psql -U airflow -d airflow -tAc \
    "SELECT state FROM dag_run
     WHERE dag_id = '$DAG_ID' AND run_id = '$RUN_ID';" 2>/dev/null | tr -d ' \r'
}

deadline=$(( $(date +%s) + TIMEOUT_SECONDS ))
previous_state=""
while :; do
  state=$(run_state || true)
  if [ -n "$state" ] && [ "$state" != "$previous_state" ]; then
    echo "   état : $state"
    previous_state="$state"
  fi
  case "$state" in
    success) echo "✓ $DAG_ID terminé avec succès"; exit 0 ;;
    failed)
      echo "✗ $DAG_ID a échoué. Tâches :" >&2
      airflow_cli tasks states-for-dag-run "$DAG_ID" "$RUN_ID" >&2 || true
      echo "   Logs : docker compose logs airflow-scheduler" >&2
      exit 1 ;;
  esac
  [ "$(date +%s)" -lt "$deadline" ] || {
    echo "✗ délai dépassé (${TIMEOUT_SECONDS}s) en attendant $DAG_ID" >&2
    exit 1; }
  sleep 15
done
