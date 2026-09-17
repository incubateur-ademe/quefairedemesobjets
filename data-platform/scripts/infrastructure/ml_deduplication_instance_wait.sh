#!/bin/bash
# Wait until the ml-deduplication inference instance is running AND cloud-init
# has completed (Docker installed + inference image pulled).
#
# Readiness is detected via SSH: once we can connect and `docker image inspect`
# returns the image, cloud-init is done. Requires an SSH private key (see
# ML_DEDUPLICATION_SSH_KEY env / Airflow secret) and the public key injected at creation.
#
# Prints the instance public IP once ready.

set -euo pipefail

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT must be set (prod|preprod)}"
PREFIX="${PREFIX:-lvao}"
ZONE="${ZONE:-fr-par-1}"
INSTANCE_NAME="${PREFIX}-${ENVIRONMENT}-ml-deduplication"
SSH_KEY="${ML_DEDUPLICATION_SSH_KEY:?ML_DEDUPLICATION_SSH_KEY (path to SSH private key) must be set}"
SSH_USER="${ML_DEDUPLICATION_SSH_USER:-root}"
IMAGE_REF="${ML_DEDUPLICATION_IMAGE:?ML_DEDUPLICATION_IMAGE must be set (full registry image ref)}"
TIMEOUT="${ML_DEDUPLICATION_WAIT_TIMEOUT:-600}"
POLL_INTERVAL="${ML_DEDUPLICATION_POLL_INTERVAL:-15}"

ssh_cmd() {
  ssh -i "${SSH_KEY}" \
      -o StrictHostKeyChecking=no \
      -o UserKnownHostsFile=/dev/null \
      -o ConnectTimeout=10 \
      "${SSH_USER}@${1}" "${2}"
}

# 1. Wait for the server to be running
echo "ml-deduplication: waiting for instance ${INSTANCE_NAME} to be running…"
scw instance server wait zone="${ZONE}" name="${INSTANCE_NAME}" >/dev/null 2>&1 || true

# Get the public IP
public_ip="$(scw instance server list zone="${ZONE}" -o json \
  | jq -r ".[] | select(.name==\"${INSTANCE_NAME}\") | .public_ip.address" | head -n1)"
[ -n "${public_ip}" ] || { echo "ml-deduplication: ERROR no public IP for ${INSTANCE_NAME}"; exit 1; }

# 2. Wait for cloud-init to finish (SSH reachable + image present)
echo "ml-deduplication: waiting for cloud-init + image pull on ${public_ip}…"
deadline=$(( $(date +%s) + TIMEOUT ))
while [ "$(date +%s)" -lt "${deadline}" ]; do
  if ssh_cmd "${public_ip}" "docker image inspect '${IMAGE_REF}' >/dev/null 2>&1"; then
    echo "ml-deduplication: instance ${public_ip} ready (image ${IMAGE_REF} present)"
    echo "${public_ip}"
    exit 0
  fi
  sleep "${POLL_INTERVAL}"
done

echo "ml-deduplication: ERROR timed out waiting for instance readiness" >&2
exit 1
