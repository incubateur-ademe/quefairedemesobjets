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

# Log all cloud-init output (including runcmd) so failures are visible in
# /var/log/cloud-init-output.log.
output:
  all: "| tee -a /var/log/cloud-init-output.log"

write_files:
  - path: /etc/ml-deduplication.env
    content: |
      REGISTRY_IMAGE=${registry_image}
      REGISTRY=${registry}
      SCW_ACCESS_KEY=${scw_access_key}
      SCW_SECRET_KEY=${scw_secret_key}

runcmd:
  # Single shell script: cloud-init runs each runcmd entry in its own shell
  # (via /bin/sh, dash on Ubuntu), so all provisioning steps share one process
  # (env sourcing persists). Use only POSIX-safe shell options: `set -o
  # pipefail` is a bash-ism that would make dash abort this block immediately,
  # silently skipping every provisioning step below.
  - |
    set -eu
    if [ -n "${BASH_VERSION:-}" ]; then set -o pipefail; fi
    . /etc/ml-deduplication.env

    # 0. Authorize the DAG's SSH key for root. Scaleway's Ubuntu images log in
    #    as root, and cloud-init's ssh_authorized_keys directive only targets the
    #    default non-root user. Also, Scaleway's scw-fetch-ssh-keys regenerates
    #    /root/.ssh/authorized_keys at every boot from project keys + the file
    #    /root/.ssh/instance_keys, so appending to authorized_keys directly would
    #    be wiped on reboot. Instead, drop the key into instance_keys (imported by
    #    scw-fetch-ssh-keys) and regenerate authorized_keys to include it now.
    mkdir -p /root/.ssh
    chmod 0700 /root/.ssh
    grep -qxF '${ssh_public_key}' /root/.ssh/instance_keys 2>/dev/null \
      || printf '%s\n' '${ssh_public_key}' >> /root/.ssh/instance_keys
    chmod 0600 /root/.ssh/instance_keys
    scw-fetch-ssh-keys --upgrade || true

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
    echo "$SCW_SECRET_KEY" | docker login "$REGISTRY" -u nologin --password-stdin

    # 3. Pull the inference image so a later `docker run` starts instantly
    docker pull "$REGISTRY_IMAGE"

    # 4. Report readiness: sentinel file the DAG polls for over SSH/scaleway
    touch /var/lib/ml-deduplication-ready
