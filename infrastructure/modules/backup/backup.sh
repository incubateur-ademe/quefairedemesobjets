#!/bin/sh
# Daily backup, run by the Serverless Job of the `backup` stack.
#
# Dumps each database of $DATABASES ("<instance-id>/<database>", space
# separated) and mirrors each bucket of $BUCKETS into $BACKUP_BUCKET. Everything
# is encrypted by rclone before it leaves the job: the bucket only ever holds
# ciphertext, so it can move to another provider by changing the `s3` remote.
#
# Restore: docs/reference/security/backups.md
set -eu

SCW_VERSION=2.66.0
SCW_SHA256=4d7891fe42ea4d4507fc50df678e9acc000d00780074fb38618ea69d0789fb14 # pragma: allowlist secret
RETENTION_DAYS=30

# ponytail: scw is downloaded at each run, so a run fails when GitHub is
# unreachable. Bake an image into the ns-qfdmo registry if that ever happens.
wget -qO /usr/local/bin/scw \
  "https://github.com/scaleway/scaleway-cli/releases/download/v${SCW_VERSION}/scaleway-cli_${SCW_VERSION}_linux_amd64"
echo "${SCW_SHA256}  /usr/local/bin/scw" | sha256sum -c -
chmod +x /usr/local/bin/scw

export RCLONE_CONFIG_S3_TYPE=s3
export RCLONE_CONFIG_S3_PROVIDER=Scaleway
export RCLONE_CONFIG_S3_REGION="$SCW_DEFAULT_REGION"
export RCLONE_CONFIG_S3_ENDPOINT="s3.${SCW_DEFAULT_REGION}.scw.cloud"
export RCLONE_CONFIG_S3_ACCESS_KEY_ID="$SCW_ACCESS_KEY"
export RCLONE_CONFIG_S3_SECRET_ACCESS_KEY="$SCW_SECRET_KEY"
export RCLONE_CONFIG_BACKUP_TYPE=crypt
export RCLONE_CONFIG_BACKUP_REMOTE="s3:${BACKUP_BUCKET}"
export RCLONE_CONFIG_BACKUP_FILENAME_ENCRYPTION=off
export RCLONE_CONFIG_BACKUP_DIRECTORY_NAME_ENCRYPTION=false
RCLONE_CONFIG_BACKUP_PASSWORD="$(rclone obscure "$ENCRYPTION_PASSWORD")"
export RCLONE_CONFIG_BACKUP_PASSWORD

day="$(date -u +%Y-%m-%d)"
# The dump kept by Scaleway is only a staging copy: it expires on its own.
expires_at="$(date -u -d "@$(($(date +%s) + 86400))" +%Y-%m-%dT%H:%M:%SZ)"

for target in $DATABASES; do
  instance_id="${target%/*}"
  database="${target#*/}"
  echo "Database ${database}: dump"
  backup_id="$(scw rdb backup create instance-id="$instance_id" database-name="$database" \
    name="backup-${database}-${day}" expires-at="$expires_at" --wait -o template='{{ .ID }}')"
  url="$(scw rdb backup export "$backup_id" --wait -o template='{{ .DownloadURL }}')"
  echo "Database ${database}: copy to the backup bucket"
  rclone copyurl "$url" "backup:db/${database}/${day}.dump"
done

for bucket in $BUCKETS; do
  echo "Bucket ${bucket}: sync"
  rclone sync "s3:${bucket}" "backup:buckets/${bucket}"
done

rclone delete --min-age "${RETENTION_DAYS}d" backup:db
echo "Backup done"
