#!/usr/bin/env bash
# Destroy the Scaleway resources of one or more preview environments,
# looked up by naming convention (no terraform state needed):
#   container  lvao-pr-<n>-webapp   in the qfdmod-preview namespace
#   database   preview_pr_<n>       on the lvao-preprod-webapp RDB instance
#   user       preview_pr_<n>       idem
#   bucket     lvao-pr-<n>-media
#   tf state   s3://lvao-terraform-state/preview/pr-<n>/
#
# Usage: preview_destroy.sh [--dry-run] <pr_number> [<pr_number> ...]
# Needs: scw (authenticated), aws (S3 creds in AWS_* env vars), jq.
# Every step is idempotent: a missing resource is not an error.
set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then DRY_RUN=true; shift; fi
[[ $# -ge 1 ]] || { echo "usage: $0 [--dry-run] <pr_number>..." >&2; exit 2; }

REGION="${SCW_DEFAULT_REGION:-fr-par}"
S3_ENDPOINT="https://s3.${REGION}.scw.cloud"
STATE_BUCKET="lvao-terraform-state"

NAMESPACE_ID=$(scw container namespace list name=qfdmod-preview region="$REGION" -o json | jq -r '.[0].id')
INSTANCE_ID=$(scw rdb instance list name=lvao-preprod-webapp region="$REGION" -o json | jq -r '.[0].id')
[[ "$NAMESPACE_ID" != "null" && "$INSTANCE_ID" != "null" ]] \
  || { echo "ERROR: preview namespace or preprod RDB instance not found" >&2; exit 1; }

run() {
  if $DRY_RUN; then echo "    [dry-run] $*"; else "$@" > /dev/null; fi
}

for pr in "$@"; do
  [[ "$pr" =~ ^[0-9]+$ ]] || { echo "ERROR: invalid PR number '$pr'" >&2; exit 2; }
  echo "→ pr-$pr"

  container_id=$(scw container container list namespace-id="$NAMESPACE_ID" name="lvao-pr-$pr-webapp" region="$REGION" -o json \
    | jq -r '.[0].id // empty')
  if [[ -n "$container_id" ]]; then
    echo "  container lvao-pr-$pr-webapp ($container_id)"
    run scw container container delete "$container_id" region="$REGION"
  fi

  if scw rdb database list instance-id="$INSTANCE_ID" name="preview_pr_$pr" -o json \
       | jq -e --arg n "preview_pr_$pr" 'any(.[]; .name == $n)' > /dev/null; then
    echo "  database preview_pr_$pr"
    run scw rdb database delete instance-id="$INSTANCE_ID" name="preview_pr_$pr"
  fi

  if scw rdb user list instance-id="$INSTANCE_ID" name="preview_pr_$pr" -o json \
       | jq -e --arg n "preview_pr_$pr" 'any(.[]; .name == $n)' > /dev/null; then
    echo "  user preview_pr_$pr"
    run scw rdb user delete instance-id="$INSTANCE_ID" name="preview_pr_$pr"
  fi

  if scw object bucket list region="$REGION" -o json | jq -e --arg b "lvao-pr-$pr-media" 'any(.[]; .Name == $b)' > /dev/null; then
    echo "  bucket lvao-pr-$pr-media"
    run scw object bucket delete "lvao-pr-$pr-media" region="$REGION"
  fi

  echo "  state s3://$STATE_BUCKET/preview/pr-$pr/"
  run aws --endpoint-url "$S3_ENDPOINT" s3 rm "s3://$STATE_BUCKET/preview/pr-$pr/" --recursive --quiet
done
