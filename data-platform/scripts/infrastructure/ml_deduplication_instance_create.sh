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

ENVIRONMENT="${ENVIRONMENT:?ENVIRONMENT must be set (prod|preprod)}"
PREFIX="${PREFIX:-lvao}"
ZONE="${ZONE:-fr-par-1}"
INSTANCE_NAME="${PREFIX}-${ENVIRONMENT}-ml-deduplication"
SECURITY_GROUP_NAME="${INSTANCE_NAME}-sg"
INSTANCE_TYPE="${ML_DEDUPLICATION_INSTANCE_TYPE:-PRO2-XXS}"
VOLUME_SIZE="${ML_DEDUPLICATION_VOLUME_SIZE:-60}"

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
  image=ubuntu_jammy \
  name="${INSTANCE_NAME}" \
  root-volume="${VOLUME_SIZE}GB" \
  ip=new \
  security-group-id="${security_group_id}" \
  cloud-init="@${tmp_cloud_init}" \
  tags.0="${ENVIRONMENT}" \
  tags.1="${PREFIX}" \
  tags.2=ml-deduplication \
  tags.3=inference \
  -o json | jq -r '.server.id')"

echo "ml-deduplication: instance created: ${instance_id}"
echo "${instance_id}"
