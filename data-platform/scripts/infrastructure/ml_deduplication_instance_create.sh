#!/bin/bash
# Create the ml-deduplication inference instance on Scaleway, provisioned with
# Docker + the inference image via cloud-init (user-data).
#
# Idempotent: if an instance with the expected name already exists and is not
# terminating, it is reused. Prints the instance ID.
#
# Requires the scw CLI and the SCW_* environment variables (already present in
# the Airflow scheduler container).

set -euo pipefail

# Local mode: no Scaleway instance is needed, so this is a no-op.
if [ "${ML_DEDUPLICATION_RUN_LOCAL:-0}" = "1" ] || [ "${ML_DEDUPLICATION_RUN_LOCAL:-0}" = "true" ]; then
  echo "ml-deduplication: local mode, skipping instance creation"
  exit 0
fi

# Route the whole ml-deduplication infrastructure process through the dedicated
# _INFRA Scaleway credentials (exposed as env vars by the scheduler container
# secret). The scw CLI and the cloud-init registry login read SCW_ACCESS_KEY /
# SCW_SECRET_KEY, so we map the infra credentials onto those standard names.
export SCW_ACCESS_KEY="${SCW_ACCESS_KEY_INFRA:?SCW_ACCESS_KEY_INFRA must be set (infra credentials)}"
export SCW_SECRET_KEY="${SCW_SECRET_KEY_INFRA:?SCW_SECRET_KEY_INFRA must be set (infra credentials)}"

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT must be set (prod|preprod)}"
PREFIX="${PREFIX:-lvao}"
INSTANCE_NAME="${PREFIX}-${ENVIRONMENT}-ml-deduplication"
SECURITY_GROUP_NAME="${INSTANCE_NAME}-sg"
INSTANCE_TYPE="${ML_DEDUPLICATION_INSTANCE_TYPE:-L4-1-24G}"
VOLUME_SIZE="${ML_DEDUPLICATION_VOLUME_SIZE:-512GB}"

# Candidate zones. GPU commercial types (L4, H100, ...) are frequently out of
# stock in a given zone, so we pick the first zone where the instance type is
# actually available. An explicitly set ZONE is tried first, then the defaults.
DEFAULT_ZONES=("fr-par-1" "fr-par-2" "pl-waw-2")
CANDIDATE_ZONES=()
if [ -n "${ZONE:-}" ]; then
  CANDIDATE_ZONES+=("${ZONE}")
fi
for z in "${DEFAULT_ZONES[@]}"; do
  if [ "${ZONE:-}" != "${z}" ]; then
    CANDIDATE_ZONES+=("${z}")
  fi
done

# Pick the first zone where the instance type is available. An instance type
# with availability != "available" (e.g. "shortage", "scarce") may fail to be
# created or be out of stock in that zone.
ZONE=""
for z in "${CANDIDATE_ZONES[@]}"; do
  availability="$(scw instance server-type list zone="${z}" -o json 2>/dev/null \
    | jq -r ".[] | select(.name==\"${INSTANCE_TYPE}\") | .availability" | head -n1 || true)"
  echo "ml-deduplication: instance type ${INSTANCE_TYPE} availability in ${z}: ${availability:-unknown}"
  if [ "${availability}" = "available" -o "${availability}" = "scarce" ]; then
    ZONE="${z}"
    break
  fi
done

if [ -z "${ZONE}" ]; then
  echo "ml-deduplication: ERROR instance type ${INSTANCE_TYPE} is not available in any zone (${CANDIDATE_ZONES[*]})" >&2
  exit 1
fi

echo "ml-deduplication: using zone ${ZONE}"

# OS image for the instance. Defaults to the Ubuntu 24.04 Noble GPU image
# ("Ubuntu Noble GPU OS 13 (Nvidia)") which ships NVIDIA drivers — required for
# GPU instance types (L4, H100, ...). Plain CPU images (ubuntu_jammy) are not
# offered for GPU commercial types.
IMAGE_LABEL="${ML_DEDUPLICATION_OS_IMAGE:-ubuntu_noble_gpu_os_13_nvidia}"

# Inference image published by CI (single full reference, e.g.
# rg.fr-par.scw.cloud/ns-.../ml-deduplication-inference:latest)
REGISTRY_IMAGE="${ML_DEDUPLICATION_IMAGE:?ML_DEDUPLICATION_IMAGE must be set (full registry image ref)}"
REGISTRY="${REGISTRY_IMAGE%%/*}"

# Canonical cloud-init shared with the DAG. Baked into the scheduler image at
# this path (see data-platform/airflow-scheduler.Dockerfile).
CLOUD_INIT_TPL="/opt/airflow/scripts/infrastructure/ml_deduplication_cloud_init.tpl"

# Public key injected into the instance so the DAG can SSH in to drive it
# (wait for readiness + run inference). See ML_DEDUPLICATION_SSH_KEY (private key).
SSH_PUB_KEY="${ML_DEDUPLICATION_SSH_PUB_KEY:?ML_DEDUPLICATION_SSH_PUB_KEY must be set}"

# Scaleway's scw-fetch-ssh-keys imports keys from server tags named
# "AUTHORIZED_KEY=<pubkey>" (spaces replaced with underscores). This is more
# reliable than cloud-init injection because the tag is set at the API level and
# fetched at every boot, and it also works with the image's own user provisioning.
AUTHORIZED_KEY_TAG="AUTHORIZED_KEY=$(printf '%s' "${SSH_PUB_KEY}" | tr ' ' '_')"

render_user_data() {
  # Replace the brace-delimited `${var}` placeholders in the cloud-init template.
  sed \
    -e "s|\${registry_image}|${REGISTRY_IMAGE}|g" \
    -e "s|\${registry}|${REGISTRY}|g" \
    -e "s|\${scw_access_key_infra}|${SCW_ACCESS_KEY_INFRA:-}|g" \
    -e "s|\${scw_secret_key_infra}|${SCW_SECRET_KEY_INFRA:-}|g" \
    -e "s|\${ssh_public_key}|${SSH_PUB_KEY}|g" \
    "${CLOUD_INIT_TPL}"
}

existing_id="$(scw instance server list zone="${ZONE}" -o json 2>/dev/null \
  | jq -r ".[] | select(.name==\"${INSTANCE_NAME}\") | select(.state!=\"stopped\") | .id" | head -n1 || true)"

if [ -n "${existing_id}" ]; then
  echo "ml-deduplication: instance ${INSTANCE_NAME} already exists (${existing_id}), reusing it"
  echo "${ZONE}"
  exit 0
fi

# Locked-down security group (default drop, allow SSH). Idempotent by name.
security_group_id="$(scw instance security-group list zone="${ZONE}" -o json 2>/dev/null \
  | jq -r ".[] | select(.name==\"${SECURITY_GROUP_NAME}\") | .id" | head -n1 || true)"
if [ -z "${security_group_id}" ]; then
  security_group_id="$(scw instance security-group create \
    zone="${ZONE}" \
    name="${SECURITY_GROUP_NAME}" \
    description="Security group for the ml-deduplication inference instance" \
    inbound-default-policy=drop \
    outbound-default-policy=accept \
    -o json | jq -r '.security_group.id')"
  scw instance security-group set-rules \
    zone="${ZONE}" \
    security-group-id="${security_group_id}" \
    rules.0.action=accept \
    rules.0.protocol=TCP \
    rules.0.direction=inbound \
    rules.0.ip-range=0.0.0.0/0 \
    rules.0.dest-port-from=22 \
    rules.0.dest-port-to=22 \
    >/dev/null
  echo "ml-deduplication: security group ${SECURITY_GROUP_NAME} created (${security_group_id})"
fi

echo "ml-deduplication: creating instance ${INSTANCE_NAME} (${INSTANCE_TYPE})…"

user_data="$(render_user_data)"
tmp_cloud_init="$(mktemp)"
trap 'rm -f "${tmp_cloud_init}"' EXIT
printf '%s\n' "${user_data}" > "${tmp_cloud_init}"

instance_id="$(scw instance server create \
  zone="${ZONE}" \
  type="${INSTANCE_TYPE}" \
  image="${IMAGE_LABEL}" \
  name="${INSTANCE_NAME}" \
  ip=new \
  security-group-id="${security_group_id}" \
  root-volume=b:${VOLUME_SIZE} \
  cloud-init="@${tmp_cloud_init}" \
  tags.0="${ENVIRONMENT}" \
  tags.1="${PREFIX}" \
  tags.2=ml-deduplication \
  tags.3=inference \
  tags.4="${AUTHORIZED_KEY_TAG}" \
  -o json | jq -r '.server.id')"

echo "ml-deduplication: instance created: ${instance_id}"
# Last line of stdout is pushed as XCom by the BashOperator and read back by
# the wait/run/destroy scripts to know which zone the instance lives in.
echo "${ZONE}"
