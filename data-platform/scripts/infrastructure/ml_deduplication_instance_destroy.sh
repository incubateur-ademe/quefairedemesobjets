#!/bin/bash
# Terminate the ml-deduplication inference instance on Scaleway, plus its
# reserved public IP (if allocated by this flow). Idempotent: no-op if the
# instance no longer exists.

set -euo pipefail

# Local mode: no Scaleway instance was created, so this is a no-op.
if [ "${ML_DEDUPLICATION_RUN_LOCAL:-0}" = "1" ] || [ "${ML_DEDUPLICATION_RUN_LOCAL:-0}" = "true" ]; then
  echo "ml-deduplication: local mode, skipping instance termination"
  exit 0
fi

# Route the whole ml-deduplication infrastructure process through the dedicated
# _INFRA Scaleway credentials (exposed as env vars by the scheduler container
# secret). The scw CLI reads SCW_ACCESS_KEY / SCW_SECRET_KEY, so we map the
# infra credentials onto those standard names.
export SCW_ACCESS_KEY="${SCW_ACCESS_KEY_INFRA:?SCW_ACCESS_KEY_INFRA must be set (infra credentials)}"
export SCW_SECRET_KEY="${SCW_SECRET_KEY_INFRA:?SCW_SECRET_KEY_INFRA must be set (infra credentials)}"

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT must be set (prod|preprod)}"
PREFIX="${PREFIX:-lvao}"
# Zone chosen at instance creation (propagated via XCom as ML_DEDUPLICATION_ZONE).
ZONE="${ML_DEDUPLICATION_ZONE:-${ZONE:-fr-par-2}}"
INSTANCE_NAME="${PREFIX}-${ENVIRONMENT}-ml-deduplication"
SECURITY_GROUP_NAME="${INSTANCE_NAME}-sg"

instance_id="$(scw instance server list zone="${ZONE}" -o json 2>/dev/null \
  | jq -r ".[] | select(.name==\"${INSTANCE_NAME}\") | .id" | head -n1 || true)"

if [ -n "${instance_id}" ]; then
  echo "ml-deduplication: terminating instance ${INSTANCE_NAME} (${instance_id})…"
  # with-ip=true also releases the flexible IP allocated at creation (ip=new).
  scw instance server terminate zone="${ZONE}" server-id="${instance_id}" with-ip=true >/dev/null 2>&1 || true
  echo "ml-deduplication: instance terminated"
else
  echo "ml-deduplication: no instance ${INSTANCE_NAME} to terminate"
fi

security_group_id="$(scw instance security-group list zone="${ZONE}" -o json 2>/dev/null \
  | jq -r ".[] | select(.name==\"${SECURITY_GROUP_NAME}\") | .id" | head -n1 || true)"
if [ -n "${security_group_id}" ]; then
  echo "ml-deduplication: deleting security group ${SECURITY_GROUP_NAME} (${security_group_id})…"
  scw instance security-group delete "${security_group_id}" zone="${ZONE}" >/dev/null 2>&1 || true
  echo "ml-deduplication: security group deleted"
else
  echo "ml-deduplication: no security group ${SECURITY_GROUP_NAME} to delete"
fi
