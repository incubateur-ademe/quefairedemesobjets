#!/usr/bin/env bash
# Container entrypoint: runs the same steps as bin/post_deploy (Scalingo),
# then starts nginx + gunicorn.
#
# Nginx listens on the Scaleway container port (8000) and proxies to
# gunicorn on 127.0.0.1:8001, matching production's two-tier setup.
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

# Start nginx in the background (proxies :8000 → :8001).
# If nginx dies, the liveness probe on :8000 will fail and Scaleway
# restarts the container.
nginx -g 'daemon off;' &

exec gunicorn core.wsgi \
  --bind "127.0.0.1:8001" \
  --timeout 120 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --max-requests 1000 \
  --max-requests-jitter 100

