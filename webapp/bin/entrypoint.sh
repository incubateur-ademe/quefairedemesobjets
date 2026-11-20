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
