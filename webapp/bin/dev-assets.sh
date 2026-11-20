#!/bin/sh
# Command of the local `assets` service.
#
# node_modules live in Docker volumes, which outlive the image. They are
# reinstalled whenever package-lock.json differs from the one they were
# installed from (first start, git pull, npm install).
set -eu

cd /app

stamp=node_modules/.package-lock.sha256
if ! sha256sum -c "$stamp" >/dev/null 2>&1; then
  npm ci
  sha256sum package-lock.json > "$stamp"
fi

[ -d webapp/static/compiled/revue ] || npm -w webapp/revue-front run build

# A cache of its own: sharing .parcel-cache with a host build serves stale bundles
exec npm -w webapp run watch -- --cache-dir /tmp/parcel-cache
