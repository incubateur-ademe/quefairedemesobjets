#!/usr/bin/env bash
# Container entrypoint for preview environments.
#
# Nginx listens on the Scaleway container port (8000) and proxies to
# gunicorn on 127.0.0.1:8001, matching production's two-tier setup.
set -euo pipefail


if [ "${RUN_MIGRATIONS_ON_START:-true}" = "true" ]; then
  echo "Applying database migrations..."
  python manage.py migrate --noinput
fi

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
