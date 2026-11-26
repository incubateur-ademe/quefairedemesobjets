#!/usr/bin/env bash
# Container entrypoint, shared by the webapp and worker containers.
#
# CONTAINER_ROLE=worker  → django-tasks worker, next to an HTTP listener
#                          (Scaleway needs one on the port for its probe)
# anything else (default) → gunicorn on :$PORT, behind the nginx gateway
set -euo pipefail

if [[ "${CONTAINER_ROLE:-web}" == "worker" ]]; then
  # db_worker stays in the foreground so that if it dies the container exits
  # and Scaleway restarts it. The listener answers 200 with an empty listing;
  # stderr kept, so that a failed bind shows in the logs.
  python -m http.server "${PORT:-8000}" --bind 0.0.0.0 \
    --directory "$(mktemp -d)" >/dev/null &
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

# Same settings as bin/start on Scalingo. Keep-alive: 75 s, the default of
# the nginx that faced the Scaleway edge before (gunicorn's is 2 s).
exec gunicorn core.wsgi \
  --bind "0.0.0.0:${PORT:-8000}" \
  --worker-class gthread \
  --preload \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --max-requests 10000 \
  --max-requests-jitter 2500 \
  --keep-alive "${GUNICORN_KEEPALIVE:-75}"
