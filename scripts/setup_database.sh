#!/usr/bin/env bash
#
# Fills the local `webapp` database when it is empty. Called by `make setup`.
#   1. SAMPLE_DB_URI (environment or .env): the sample database, small and
#      fast, the one the CI restores
#   2. otherwise, a configured Scaleway CLI: the latest production backup
#   3. otherwise the database stays empty
set -euo pipefail

cd "$(dirname "$0")/.."

acteur_count() {
  docker compose exec -T webapp-db psql -U webapp -d webapp -tAc \
    "select count(*) from qfdmo_displayedacteur" 2>/dev/null || echo 0
}

count=$(acteur_count)
if [ "$count" -gt 0 ]; then
  echo "✓ Base webapp déjà peuplée ($count acteurs affichés)"
  exit 0
fi

SAMPLE_DB_URI="${SAMPLE_DB_URI:-$(sed -n 's/^SAMPLE_DB_URI=//p' .env 2>/dev/null | tail -1 || true)}"
export SAMPLE_DB_URI

if [ -n "$SAMPLE_DB_URI" ]; then
  echo "Base webapp vide : restauration de la base d'échantillon…"
  # Dumped and restored inside the container: no Postgres client on the host.
  # pg_restore reports the objects it cannot drop as errors, as in the CI.
  docker compose exec -T -e SAMPLE_DB_URI webapp-db sh -c \
    'pg_dump -Fc "$SAMPLE_DB_URI" | pg_restore -U webapp -d webapp --clean --if-exists --no-owner --no-privileges' \
    || true
  make -C webapp migrate
  count=$(acteur_count)
  [ "$count" -gt 0 ] || { echo "✗ La restauration de l'échantillon a échoué : vérifiez SAMPLE_DB_URI" >&2; exit 1; }
  echo "✓ Échantillon restauré ($count acteurs affichés)"
elif command -v scw >/dev/null && scw rdb instance list >/dev/null 2>&1; then
  echo "Base webapp vide : restauration du dernier backup de production (environ 10 Go)…"
  make db-restore-local-from-prod USE_LATEST_BACKUP=true
else
  cat <<'MSG'
⚠ La base webapp est vide. Pour la peupler, au choix :
  - SAMPLE_DB_URI=… dans .env (base d'échantillon, rapide), puis `make setup`
  - le client Scaleway configuré (`scw init`), puis `make setup` : production
MSG
fi
