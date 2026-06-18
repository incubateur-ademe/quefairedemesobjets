#!/usr/bin/env bash
# Container entrypoint: runs the same steps as bin/post_deploy (Scalingo),
# then starts gunicorn with the same flags as bin/start.
set -euo pipefail

python manage.py createcachetable
python manage.py migrate

# TEMPORARY, required to have search function after deploy
python manage.py enable_unaccent
python manage.py enable_trigram

python manage.py clearsessions
python manage.py clear_cache --all

# Sets up cross-database postgres schemas for dbt. Requires a reachable
# warehouse database, which preview environments don't have.
if [[ -n "${DB_WAREHOUSE:-}" ]]; then
  python manage.py create_remote_db_server
else
  echo "DB_WAREHOUSE not set, skipping create_remote_db_server"
fi

# Purge orphan base SearchTerm index entries (django-modelsearch #58).
# May fail if the sample DB dump has a different migration state than the
# current code — tolerated because it's non-critical for previews.
python manage.py purge_orphan_searchterm_index || true

exec gunicorn core.wsgi \
  --bind "0.0.0.0:${PORT:-8000}" \
  --timeout 120 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --max-requests 1000 \
  --max-requests-jitter 100

