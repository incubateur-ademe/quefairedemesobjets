#!/usr/bin/env bash
# Container entrypoint, shared by the webapp and worker containers.
#
# CONTAINER_ROLE=worker  → django-tasks worker behind a stub nginx (Scaleway
#                          needs an HTTP listener on the port for its probe)
# anything else (default) → nginx :8000 proxying to gunicorn :8001
set -euo pipefail

if [[ "${CONTAINER_ROLE:-web}" == "worker" ]]; then
  # db_worker stays in the foreground so that if it dies the container exits
  # and Scaleway restarts it.
  printf 'server { listen 8000; access_log off; location / { return 200 "ok"; } }\n' \
    > /etc/nginx/servers.conf
  nginx -g 'daemon off;' &
  exec python manage.py db_worker
fi

# Previews only: preprod and prod run bin/post_deploy as a CI step before the
# image is rolled out (RUN_MIGRATIONS_ON_START=false).
if [ "${RUN_MIGRATIONS_ON_START:-true}" = "true" ]; then
  echo "Applying database migrations..."
  python manage.py migrate --noinput
  python manage.py populate_libelle_court
  python manage.py seed_lieux_de_depot
  # TODO: remove once the consignes grid is live in production.
  # Grid of consignes of the live fiches, as bin/post_deploy does in
  # production: the preview database is only seeded once, so redeploys
  # would otherwise never convert the fiches. No-op once they have one.
  python manage.py generate_consignes || echo "generate_consignes failed, starting anyway" >&2
fi

# Start nginx in the background (proxies :8000 → :8001).
# If nginx dies, the liveness probe on :8000 will fail and Scaleway
# restarts the container.
nginx -g 'daemon off;' &

# Same settings as bin/start on Scalingo.
exec gunicorn core.wsgi \
  --bind "127.0.0.1:8001" \
  --worker-class gthread \
  --preload \
  --timeout 120 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --max-requests 10000 \
  --max-requests-jitter 2500
