#!/usr/bin/env bash
# Container entrypoint, shared by the webapp and worker containers.
#
# CONTAINER_ROLE=worker  → django-tasks worker behind a stub nginx (Scaleway
#                          needs an HTTP listener on the port for its probe)
# anything else (default) → nginx :8000 proxying to gunicorn :8001
#
# Django management commands (migrate, createcachetable) run as a CI step
# before the image is rolled out, not on every cold start.
set -euo pipefail

if [[ "${CONTAINER_ROLE:-web}" == "worker" ]]; then
  # Stub listener for the liveness probe. db_worker stays in the foreground
  # so that if it dies the container exits and Scaleway restarts it.
  printf 'server { listen 8000; access_log off; location / { return 200 "ok"; } }\n' \
    > /etc/nginx/servers.conf
  nginx -g 'daemon off;' &
  exec python manage.py db_worker
fi

# Render servers.conf.erb from the container env (ENVIRONMENT, BASE_DOMAIN,
# NGINX_ALLOW_ALL_HOSTS, NGINX_DISABLE_CACHE), same template as Scalingo and
# the local lvao-proxy image. PORT / UPSTREAM_HOST are fixed by this image.
PORT=8000 UPSTREAM_HOST=127.0.0.1:8001 \
  ruby -e "require 'erb'; puts ERB.new(File.read('/etc/nginx/servers.conf.erb')).result(binding)" \
  > /etc/nginx/servers.conf

# Start nginx in the background (proxies :8000 → :8001).
# If nginx dies, the liveness probe on :8000 fails and Scaleway restarts
# the container.
nginx -g 'daemon off;' &

# gthread, not the default sync worker: sync handles one request per worker
# start-to-finish, capping concurrency at --workers on an I/O-bound app.
# Threads are bounded by Postgres (each holds a connection for CONN_MAX_AGE,
# against a max_connections shared with Airflow), not by CPU.
exec gunicorn core.wsgi \
  --bind "127.0.0.1:8001" \
  --worker-class gthread \
  --timeout 120 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-8}" \
  --max-requests 1000 \
  --max-requests-jitter 100
