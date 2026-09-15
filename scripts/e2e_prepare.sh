#!/usr/bin/env bash
#
# Prepare the local environment for the e2e tests.
#
# Each step checks its prerequisites and stops with an explicit message on
# the first failure:
#   1. tooling, .env files, and that ports 6543/8765 belong to Docker
#   2. the Docker stack (webapp DB, warehouse DB, Airflow)
#   3. a populated `webapp` database (the source of the sample)
#   4. the postgres_fdw bridge exposing `webapp` to the warehouse
#   5. the `compute_sample_acteur` DAG, which builds `webapp_sample`
#   6. migrations, search index and JS build, run against `webapp_sample`
#
# The sample database is always built locally by the DAG; no remote dump is
# downloaded.
#
# Usage: scripts/e2e_prepare.sh [--skip-dag]
#   --skip-dag  keep the existing webapp_sample instead of rebuilding it
set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$PWD"

DAG_ID="compute_sample_acteur"
WAREHOUSE_URL="${DB_WAREHOUSE:-postgres://warehouse:warehouse@localhost:8765/warehouse}" # pragma: allowlist secret
WEBAPP_URL="${DATABASE_URL:-postgres://webapp:webapp@localhost:6543/webapp}" # pragma: allowlist secret
SAMPLE_URL="${DB_WEBAPP_SAMPLE:-postgres://webapp_sample:webapp_sample@localhost:6543/webapp_sample}" # pragma: allowlist secret

SKIP_DAG=0
[ "${1:-}" = "--skip-dag" ] && SKIP_DAG=1

step() { printf '\n\033[1;34m==> %s\033[0m\n' "$1"; }
ok()   { printf '   \033[0;32m✓\033[0m %s\n' "$1"; }
die()  { printf '   \033[0;31m✗ %s\033[0m\n' "$1" >&2; exit 1; }

# --- 1. Tooling ------------------------------------------------------------
step "Vérification des prérequis"
for bin in docker psql uv npx; do
  command -v "$bin" >/dev/null || die "$bin est introuvable dans le PATH"
done
docker info >/dev/null 2>&1 || die "le démon Docker ne répond pas"
[ -f webapp/.env ] || die "webapp/.env est absent (cp webapp/.env.template webapp/.env)"
[ -f data-platform/dags/.env ] || \
  die "data-platform/dags/.env est absent (cp data-platform/dags/.env.template data-platform/dags/.env)"
ok "outils et fichiers .env présents"

# A foreign process bound to a port that Docker publishes shadows the
# container: TCP connects, but the Postgres handshake never completes and psql
# only reports a connection timeout. Name the process instead.
for port in 6543 8765; do
  listening_pid=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | head -1 || true)
  if [ -n "$listening_pid" ]; then
    process_name=$(ps -o comm= -p "$listening_pid" 2>/dev/null || echo "?")
    case "$process_name" in
      *OrbStack*|*docker*|*com.docker*) : ;;
      *) die "le port $port est occupé par « $process_name » (PID $listening_pid), pas par Docker. Arrêtez ce process puis relancez." ;;
    esac
  fi
done
ok "ports 6543 et 8765 libres pour Docker"

# --- 2. Docker stack -------------------------------------------------------
step "Démarrage de la stack Docker (profil airflow)"
docker compose --profile airflow up -d
ok "conteneurs démarrés"

wait_for_postgres() {
  local url="$1" label="$2"
  for _ in $(seq 1 60); do
    psql "$url" -tAc 'select 1' >/dev/null 2>&1 && { ok "$label joignable"; return 0; }
    sleep 2
  done
  die "$label injoignable sur $url"
}
wait_for_postgres "$WEBAPP_URL" "base webapp"
wait_for_postgres "$WAREHOUSE_URL" "base warehouse"

# --- 3. Populated webapp database ------------------------------------------
step "Vérification de la base webapp (source de l'échantillon)"
webapp_acteur_count=$(psql "$WEBAPP_URL" -tAc \
  "select count(*) from qfdmo_displayedacteur" 2>/dev/null || echo 0)
if [ "${webapp_acteur_count:-0}" -lt 1000 ]; then
  die "la base webapp ne contient que ${webapp_acteur_count:-0} acteurs affichés.
   Restaurez d'abord la production : make db-restore-local-from-prod"
fi
ok "$webapp_acteur_count acteurs affichés dans webapp"

# --- 4. postgres_fdw bridge ------------------------------------------------
# The dbt sample models read `webapp` through the `webapp_public` foreign
# schema of the warehouse.
step "Pont postgres_fdw warehouse <-> webapp"
if ! psql "$WAREHOUSE_URL" -tAc \
     "select 1 from information_schema.tables
      where table_schema='webapp_public' limit 1" 2>/dev/null | grep -q 1; then
  ( cd webapp && uv run python manage.py create_remote_db_server )
fi
psql "$WAREHOUSE_URL" -tAc "select count(*) from webapp_public.qfdmo_displayedacteur" \
  >/dev/null 2>&1 || die "le schéma webapp_public est inutilisable depuis warehouse"
ok "schéma webapp_public lisible depuis warehouse"

# --- 5. Sample database ----------------------------------------------------
if [ "$SKIP_DAG" -eq 1 ]; then
  step "DAG ignoré (--skip-dag)"
else
  step "Construction de l'échantillon via le DAG $DAG_ID"
  "$REPO_ROOT/scripts/e2e_run_sample_dag.sh"
fi

sample_acteur_count=$(psql "$SAMPLE_URL" -tAc \
  "select count(*) from qfdmo_displayedacteur" 2>/dev/null || echo 0)
[ "${sample_acteur_count:-0}" -gt 0 ] || \
  die "la base webapp_sample est vide — consultez les logs du DAG $DAG_ID"
ok "$sample_acteur_count acteurs dans webapp_sample"

# --- 6. Webapp preparation -------------------------------------------------
# A stale Parcel cache can emit a broken bundle while the build still exits 0,
# so it is purged before every build.
step "Préparation de la webapp (migrations, index, build JS)"
rm -rf .parcel-cache webapp/.parcel-cache
make -C webapp DATABASE_URL="$SAMPLE_URL" prepare-e2e-test
ok "webapp prête"

printf '\n\033[1;32m✓ Environnement e2e prêt.\033[0m Lancez : make webapp-e2e-test\n'
