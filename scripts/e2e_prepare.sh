#!/usr/bin/env bash
#
# Prepare the local environment for the e2e tests:
#   1. start the Docker stack (webapp DB, warehouse DB, Airflow)
#   2. check that `webapp` is populated (it is the source of the sample)
#   3. expose `webapp` to the warehouse through postgres_fdw
#   4. run the `compute_sample_acteur` DAG, which builds `webapp_sample`
#   5. migrations, search index and JS build against `webapp_sample`
#
# Usage: scripts/e2e_prepare.sh [--skip-dag]
#   --skip-dag  keep the existing webapp_sample instead of rebuilding it
set -euo pipefail

cd "$(dirname "$0")/.."

# As seen from the containers
SAMPLE_URL="${DB_WEBAPP_SAMPLE:-postgres://webapp_sample:webapp_sample@lvao-webapp-db:5432/webapp_sample}" # pragma: allowlist secret

die() { echo "✗ $1" >&2; exit 1; }
webapp_psql() { docker compose exec -T lvao-webapp-db psql -U webapp -d webapp "$@"; }
warehouse_psql() { docker compose exec -T lvao-warehouse-db psql -U warehouse -d warehouse "$@"; }

# --- 1. Docker stack -------------------------------------------------------
docker compose --profile airflow up -d --build --wait

# --- 2. Populated webapp database ------------------------------------------
acteur_count=$(webapp_psql -tAc "select count(*) from qfdmo_displayedacteur" 2>/dev/null || echo 0)
[ "$acteur_count" -ge 1000 ] || die "la base webapp ne contient que $acteur_count acteurs affichés.
  Restaurez d'abord la production : make db-restore-local-from-prod"

# --- 3. postgres_fdw bridge ------------------------------------------------
# The dbt sample models read `webapp` through the `webapp_public` foreign
# schema of the warehouse.
warehouse_psql -tAc "select 1 from webapp_public.qfdmo_displayedacteur limit 1" >/dev/null 2>&1 \
  || make -C webapp create-remote-db-server

# --- 4. Sample database ----------------------------------------------------
[ "${1:-}" = "--skip-dag" ] || ./scripts/e2e_run_sample_dag.sh

# --- 5. Webapp preparation -------------------------------------------------
make -C webapp DATABASE_URL="$SAMPLE_URL" prepare-e2e-test

echo "✓ Environnement e2e prêt. Lancez : make webapp-e2e-test"
