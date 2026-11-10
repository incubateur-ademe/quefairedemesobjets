#!/usr/bin/env bash
# Wait until every given Scaleway container is `ready`.
#
# Usage: wait_container_ready.sh <container_id>...
# Ids may be `region/uuid` (Terraform) or a bare uuid.
#
# Scaleway does not restart a container whose probe fails: a slow start goes
# through `error` and back to `ready`, so only a timeout is a failure.
# Keep START_TIMEOUT_SECONDS above the startup probe budget of the slowest
# container.
set -euo pipefail

REGION="${SCW_DEFAULT_REGION:-fr-par}"
START_TIMEOUT_SECONDS="${START_TIMEOUT_SECONDS:-360}"

(($#)) || { echo "::error title=Scaleway deployment failed::no container id to wait for"; exit 1; }

for ID in "$@"; do
  ID="${ID##*/}"
  START=$SECONDS
  while true; do
    CONTAINER=$(scw container container get "$ID" region="$REGION" -o json || true)
    STATUS=$(jq -r '.status // "unknown"' <<<"$CONTAINER" 2>/dev/null || echo unknown)
    NAME=$(jq -r '.name // empty' <<<"$CONTAINER" 2>/dev/null || true)
    echo "${NAME:-$ID}: $STATUS"

    [[ "$STATUS" == "ready" ]] && break

    if ((SECONDS - START >= START_TIMEOUT_SECONDS)); then
      ERROR=$(jq -r '.error_message // "Scaleway gave no error message"' <<<"$CONTAINER" 2>/dev/null || echo "Scaleway gave no answer")
      echo "::error title=Scaleway deployment failed::${NAME:-$ID} is $STATUS after $((SECONDS - START))s: ${ERROR//$'\n'/%0A}"
      exit 1
    fi
    sleep 5
  done
done
