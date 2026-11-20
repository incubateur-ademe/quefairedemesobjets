#!/bin/sh
# Entrypoint of the local development image.
#
# The image ships the dependencies of the uv.lock it was built from. Syncing
# again costs nothing when they match, and catches up when the lockfile moved
# since (git pull, uv add) without waiting for a rebuild.
set -eu

uv sync --project /app --frozen --group dev --group webapp-dev --quiet

exec "$@"
