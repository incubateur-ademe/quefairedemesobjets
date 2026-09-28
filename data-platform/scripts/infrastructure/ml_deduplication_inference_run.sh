#!/bin/bash
# Run the ml-deduplication inference on the remote instance.
#
# The inference image reads acteurs directly from the warehouse database
# (DATABASE_CONNECTION_URI) and writes clusters + predictions back to a database
# table (--output-table), so no file transfer between Airflow and the instance
# is needed. Parameters are forwarded to the container CLI.
#
# Prints the run_id.

set -euo pipefail

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT must be set (prod|preprod)}"
PREFIX="${PREFIX:-lvao}"
ZONE="${ZONE:-fr-par-2}"
INSTANCE_NAME="${PREFIX}-${ENVIRONMENT}-ml-deduplication"
IMAGE_REF="${ML_DEDUPLICATION_IMAGE:?ML_DEDUPLICATION_IMAGE must be set (full registry image ref)}"
# Local mode: when set, we skip the remote instance entirely and run the image
# with docker directly on the machine executing this script (e.g. the local
# scheduler container with the docker socket mounted). Requires docker + a
# warehouse DB URI reachable from that machine.
RUN_LOCAL="${ML_DEDUPLICATION_RUN_LOCAL:-0}"
# Warehouse DB already exported in the scheduler container (DB_WAREHOUSE). The
# inference reads acteurs from it and writes clusters/predictions back to it.
DATABASE_CONNECTION_URI="${DATABASE_CONNECTION_URI:-${DB_WAREHOUSE:?DB_WAREHOUSE or DATABASE_CONNECTION_URI must be set}}"

ACTEURS_TABLE="${ML_DEDUPLICATION_ACTEURS_TABLE:-}"
OUTPUT_TABLE="${ML_DEDUPLICATION_OUTPUT_TABLE:-}"
RUN_ID="${ML_DEDUPLICATION_RUN_ID:-inference_$(date +%Y%m%dT%H%M%S)}"
MODEL_THRESHOLD="${ML_DEDUPLICATION_MODEL_THRESHOLD:-}"
LINKAGE_COLUMN="${ML_DEDUPLICATION_LINKAGE_COLUMN:-}"
SPLIT_BY_DEPARTEMENT="${ML_DEDUPLICATION_SPLIT_BY_DEPARTEMENT:-0}"
# Docker network to join so the container can reach the warehouse DB (defaults
# to the compose network when running from the scheduler container).
DOCKER_NETWORK="${ML_DEDUPLICATION_DOCKER_NETWORK:-}"
# Where inference parquet outputs are written (host dir mounted into the
# container). Defaults to /tmp/ml-deduplication-outputs for local runs.
OUTPUT_DIR="${ML_DEDUPLICATION_OUTPUT_DIR:-/tmp/ml-deduplication-outputs}"

# Build the container CLI arguments. We invoke the entrypoint module
# explicitly (instead of relying on the image CMD) because the CMD is in exec
# form: passing extra args after the image would REPLACE the CMD rather than
# append to it. --model-path must therefore be set here too.
PYTHON_CMD="python -m ml_deduplication.inference.xgboost.run_inference"
args="--model-path /model --output-dir /outputs --run-id ${RUN_ID}"
[ -n "${MODEL_THRESHOLD}" ] && args="${args} --model-threshold ${MODEL_THRESHOLD}"
[ -n "${LINKAGE_COLUMN}" ] && args="${args} --linkage-column ${LINKAGE_COLUMN}"
[ "${SPLIT_BY_DEPARTEMENT}" = "1" ] && args="${args} --split-by-departement"
[ -n "${OUTPUT_TABLE}" ] && args="${args} --output-table ${OUTPUT_TABLE}"
if [ -n "${ACTEURS_TABLE}" ]; then
  args="${args} --acteurs-table ${ACTEURS_TABLE}"
else
  echo "ml-deduplication: ERROR ML_DEDUPLICATION_ACTEURS_TABLE is required (DB-backed inference)" >&2
  exit 1
fi

if [ "${RUN_LOCAL}" = "1" ] || [ "${RUN_LOCAL}" = "true" ]; then
  echo "ml-deduplication: running inference locally with docker (run_id=${RUN_ID})…"
  mkdir -p "${OUTPUT_DIR}"
  # In local mode the container runs on the host network, so it needs a
  # host-reachable warehouse URI (ML_DEDUPLICATION_DATABASE_URI), not the
  # compose-internal one used by the scheduler container.
  LOCAL_DB_URI="${ML_DEDUPLICATION_DATABASE_URI:-${DATABASE_CONNECTION_URI}}"
  docker run --rm \
    -e DATABASE_CONNECTION_URI="${LOCAL_DB_URI}" \
    $( [ -n "${DOCKER_NETWORK}" ] && printf -- "--network %s" "${DOCKER_NETWORK}" ) \
    -v "${OUTPUT_DIR}":/outputs \
    "${IMAGE_REF}" ${PYTHON_CMD} ${args}
  echo "ml-deduplication: local inference done (run_id=${RUN_ID})"
  echo "${RUN_ID}"
  exit 0
fi

# --- Remote (Scaleway) path -------------------------------------------------
# Private SSH key: prefer the base64-encoded value injected as a container
# secret (ML_DEDUPLICATION_SSH_KEY_B64, e.g. from Terraform); decode it to a
# temp file. Otherwise fall back to a pre-placed key file path (ML_DEDUPLICATION_SSH_KEY).
if [ -n "${ML_DEDUPLICATION_SSH_KEY_B64:-}" ]; then
  SSH_KEY="$(mktemp)"
  chmod 0600 "${SSH_KEY}"
  printf '%s' "${ML_DEDUPLICATION_SSH_KEY_B64}" | base64 -d > "${SSH_KEY}"
  trap 'rm -f "${SSH_KEY}"' EXIT
else
  SSH_KEY="${ML_DEDUPLICATION_SSH_KEY:?ML_DEDUPLICATION_SSH_KEY (path to SSH private key) must be set}"
fi
SSH_USER="${ML_DEDUPLICATION_SSH_USER:-root}"

public_ip="$(scw instance server list zone="${ZONE}" -o json \
  | jq -r ".[] | select(.name==\"${INSTANCE_NAME}\") | .public_ip.address" | head -n1)"
[ -n "${public_ip}" ] || { echo "ml-deduplication: ERROR no instance ${INSTANCE_NAME} found"; exit 1; }

echo "ml-deduplication: running inference on ${public_ip} (run_id=${RUN_ID})…"

ssh -i "${SSH_KEY}" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    "${SSH_USER}@${public_ip}" \
    "docker run --rm \
      -e DATABASE_CONNECTION_URI='${DATABASE_CONNECTION_URI}' \
      -v /var/lib/ml-deduplication/outputs:/outputs \
      ${IMAGE_REF} ${PYTHON_CMD} ${args}"

echo "ml-deduplication: inference done (run_id=${RUN_ID})"
echo "${RUN_ID}"
