## Bucket

resource "scaleway_object_bucket" "backups" {
  name = "${var.prefix}-${var.environment}-backups"

  # A file the job overwrites or deletes stays recoverable for a month.
  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "expire-old-versions"
    enabled = true

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "scaleway_object_bucket_acl" "backups" {
  bucket = scaleway_object_bucket.backups.id
  acl    = "private"
}

resource "scaleway_object_bucket_server_side_encryption_configuration" "backups" {
  bucket = scaleway_object_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

## API key of the job

resource "scaleway_iam_application" "backup" {
  name        = "${var.prefix}-${var.environment}-backup"
  description = "Daily backup job"
}

resource "scaleway_iam_policy" "backup" {
  name           = "${var.prefix}-${var.environment}-backup"
  application_id = scaleway_iam_application.backup.id

  rule {
    project_ids = [var.project_id]
    permission_set_names = [
      "RelationalDatabasesFullAccess",
      "ObjectStorageBucketsRead",
      "ObjectStorageObjectsRead",
      "ObjectStorageObjectsWrite",
      "ObjectStorageObjectsDelete",
    ]
  }
}

resource "scaleway_iam_api_key" "backup" {
  application_id     = scaleway_iam_application.backup.id
  description        = "Daily backup job"
  default_project_id = var.project_id
}

## Secrets of the job

# Encrypts every file before upload. Without it the backups cannot be read:
# keep a copy in the team's password manager (output `encryption_password`).
resource "random_password" "encryption" {
  length  = 64
  special = false
}

locals {
  job_secrets = {
    secret-key          = scaleway_iam_api_key.backup.secret_key
    encryption-password = random_password.encryption.result
    script              = file("${path.module}/backup.sh")
  }
}

resource "scaleway_secret" "job" {
  for_each = toset(keys(local.job_secrets))

  name = each.key
  path = "/backup/${var.environment}"
}

resource "scaleway_secret_version" "job" {
  for_each = scaleway_secret.job

  secret_id = each.value.id
  data      = local.job_secrets[each.key]
}

## Job

resource "scaleway_job_definition" "backup" {
  name        = "${var.prefix}-${var.environment}-backup"
  description = "Dumps the databases and mirrors the buckets into ${scaleway_object_bucket.backups.name}"

  # Public image: Scaleway's own scaleway/cli image has no shell.
  image_uri       = "rclone/rclone:1.72.0"
  startup_command = ["/bin/sh", "/backup.sh"]
  cpu_limit       = 1120
  memory_limit    = 2048
  # Dumps are streamed from Scaleway to the bucket, nothing is written to disk.
  local_storage_capacity = 1000
  timeout                = "2h"

  cron {
    schedule = var.schedule
    timezone = "Europe/Paris"
  }

  env = {
    SCW_ACCESS_KEY              = scaleway_iam_api_key.backup.access_key
    SCW_DEFAULT_PROJECT_ID      = var.project_id
    SCW_DEFAULT_ORGANIZATION_ID = var.organization_id
    SCW_DEFAULT_REGION          = scaleway_object_bucket.backups.region
    BACKUP_BUCKET               = scaleway_object_bucket.backups.name
    BUCKETS                     = join(" ", var.buckets)
    # The provider's instance ID is <region>/<uuid>, scw wants the uuid.
    DATABASES = join(" ", [
      for database in var.databases :
      "${element(split("/", database.instance_id), 1)}/${database.name}"
    ])
  }

  secret_reference {
    secret_id      = scaleway_secret.job["secret-key"].id
    secret_version = scaleway_secret_version.job["secret-key"].revision
    environment    = "SCW_SECRET_KEY"
  }

  secret_reference {
    secret_id      = scaleway_secret.job["encryption-password"].id
    secret_version = scaleway_secret_version.job["encryption-password"].revision
    environment    = "ENCRYPTION_PASSWORD"
  }

  secret_reference {
    secret_id      = scaleway_secret.job["script"].id
    secret_version = scaleway_secret_version.job["script"].revision
    file           = "/backup.sh"
  }
}
