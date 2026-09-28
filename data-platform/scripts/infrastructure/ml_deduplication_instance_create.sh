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

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT must be set (prod|preprod)}"
PREFIX="${PREFIX:-lvao}"
ZONE="${ZONE:-fr-par-2}"
INSTANCE_NAME="${PREFIX}-${ENVIRONMENT}-ml-deduplication"
SECURITY_GROUP_NAME="${INSTANCE_NAME}-sg"
INSTANCE_TYPE="${ML_DEDUPLICATION_INSTANCE_TYPE:-L4-1-24G}"
VOLUME_SIZE="${ML_DEDUPLICATION_VOLUME_SIZE:-125}"

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
    -e "s|\${scw_access_key}|${SCW_ACCESS_KEY:-}|g" \
    -e "s|\${scw_secret_key}|${SCW_SECRET_KEY:-}|g" \
    -e "s|\${ssh_public_key}|${SSH_PUB_KEY}|g" \
    "${CLOUD_INIT_TPL}"
}

existing_id="$(scw instance server list zone="${ZONE}" -o json 2>/dev/null \
  | jq -r ".[] | select(.name==\"${INSTANCE_NAME}\") | select(.state!=\"stopped\") | .id" | head -n1 || true)"

if [ -n "${existing_id}" ]; then
  echo "ml-deduplication: instance ${INSTANCE_NAME} already exists (${existing_id}), reusing it"
  echo "${existing_id}"
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
  cloud-init="@${tmp_cloud_init}" \
  tags.0="${ENVIRONMENT}" \
  tags.1="${PREFIX}" \
  tags.2=ml-deduplication \
  tags.3=inference \
  tags.4="${AUTHORIZED_KEY_TAG}" \
  -o json | jq -r '.server.id')"

echo "ml-deduplication: instance created: ${instance_id}"
echo "${instance_id}"
