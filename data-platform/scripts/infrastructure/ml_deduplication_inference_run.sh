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
ZONE="${ZONE:-fr-par-1}"
INSTANCE_NAME="${PREFIX}-${ENVIRONMENT}-ml-deduplication"
SSH_KEY="${ML_DEDUPLICATION_SSH_KEY:?ML_DEDUPLICATION_SSH_KEY must be set}"
SSH_USER="${ML_DEDUPLICATION_SSH_USER:-root}"
IMAGE_REF="${ML_DEDUPLICATION_IMAGE:?ML_DEDUPLICATION_IMAGE must be set (full registry image ref)}"
# Warehouse DB already exported in the scheduler container (DB_WAREHOUSE). The
# inference reads acteurs from it and writes clusters/predictions back to it.
DATABASE_CONNECTION_URI="${DATABASE_CONNECTION_URI:-${DB_WAREHOUSE:?DB_WAREHOUSE or DATABASE_CONNECTION_URI must be set}}"

ACTEURS_TABLE="${ML_DEDUPLICATION_ACTEURS_TABLE:-}"
OUTPUT_TABLE="${ML_DEDUPLICATION_OUTPUT_TABLE:-}"
RUN_ID="${ML_DEDUPLICATION_RUN_ID:-inference_$(date +%Y%m%dT%H%M%S)}"
MODEL_THRESHOLD="${ML_DEDUPLICATION_MODEL_THRESHOLD:-}"
LINKAGE_COLUMN="${ML_DEDUPLICATION_LINKAGE_COLUMN:-}"
SPLIT_BY_DEPARTEMENT="${ML_DEDUPLICATION_SPLIT_BY_DEPARTEMENT:-0}"

public_ip="$(scw instance server list zone="${ZONE}" -o json \
  | jq -r ".[] | select(.name==\"${INSTANCE_NAME}\") | .public_ip.address" | head -n1)"
[ -n "${public_ip}" ] || { echo "ml-deduplication: ERROR no instance ${INSTANCE_NAME} found"; exit 1; }

echo "ml-deduplication: running inference on ${public_ip} (run_id=${RUN_ID})…"

# Build the container CLI arguments
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

ssh -i "${SSH_KEY}" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    "${SSH_USER}@${public_ip}" \
    "docker run --rm \
      -e DATABASE_CONNECTION_URI='${DATABASE_CONNECTION_URI}' \
      -v /var/lib/ml-deduplication/outputs:/outputs \
      ${IMAGE_REF} ${args}"

echo "ml-deduplication: inference done (run_id=${RUN_ID})"
echo "${RUN_ID}"
