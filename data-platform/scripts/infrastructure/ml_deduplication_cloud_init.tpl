#cloud-config
# Canonical cloud-init user-data for the ml-deduplication inference instance.
#
# Installs Docker (Engine + Compose plugin), pre-pulls the inference image so
# that a later `docker run` starts instantly, and injects the DAG's SSH public
# key so Airflow can connect to drive the instance.
#
# This single file is the source of truth. It is rendered by the Airflow DAG
# (data-platform/dags/ml_deduplication) with sed before being passed to
# `scw instance server create --cloud-init=@file`.
#
# Substituted variables (only the brace-delimited placeholders below are
# templated; everything else is left literal so cloud-init's shell can expand it
# at boot): registry_image, registry, scw_access_key, scw_secret_key,
# ssh_public_key.

ssh_authorized_keys:
  - ${ssh_public_key}

write_files:
  - path: /etc/ml-deduplication.env
    content: |
      REGISTRY_IMAGE=${registry_image}
      REGISTRY=${registry}
      SCW_ACCESS_KEY=${scw_access_key}
      SCW_SECRET_KEY=${scw_secret_key}

runcmd:
  # Single shell script: cloud-init runs each runcmd entry in its own shell, so
  # all provisioning steps share one process (env sourcing persists).
  - |
    set -euxo pipefail
    . /etc/ml-deduplication.env

    # 1. Install Docker Engine + Compose plugin (official repo)
    apt-get update
    apt-get install -y --no-install-recommends ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker

    # 2. Authenticate to the (private) Scaleway container registry
    set +x; echo "$SCW_SECRET_KEY" | docker login "$REGISTRY" -u nologin --password-stdin; set -x

    # 3. Pull the inference image so a later `docker run` starts instantly
    docker pull "$REGISTRY_IMAGE"

    # 4. Report readiness: sentinel file the DAG polls for over SSH/scaleway
    touch /var/lib/ml-deduplication-ready
