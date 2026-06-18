data "scaleway_rdb_instance" "host" {
  instance_id = var.webapp_instance_id
}

resource "random_password" "preview" {
  length  = 32
  special = true
  # Scaleway RDB requires at least one special char, digit, lowercase and
  # uppercase letter. Restricted to chars that don't need URL-encoding in
  # the postgres:// DSN built below (no @, :, /, ?, #, %).
  override_special = "-_.~!*"
  min_special      = 1
  min_numeric      = 1
  min_lower        = 1
  min_upper        = 1
}

locals {
  host = data.scaleway_rdb_instance.host.load_balancer.0.ip
  port = data.scaleway_rdb_instance.host.load_balancer.0.port

  # var.webapp_instance_id is the Terraform-style composite ID
  # ("fr-par/<uuid>"); the scw CLI's instance-id argument wants the bare
  # UUID only.
  instance_uuid = element(split("/", var.webapp_instance_id), length(split("/", var.webapp_instance_id)) - 1)

  preview_db_url = format(
    "postgresql://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
    var.preview_db_username,
    random_password.preview.result,
    local.host,
    local.port,
    var.preview_db_name,
  )
}

# Database, user and privilege are managed via the `scw` CLI instead of the
# scaleway_rdb_database/user/privilege Terraform resources: the provider hit
# a "Missing Resource Identity After Read" bug on scaleway_rdb_privilege once
# the database had been reseeded a few times, and separately the privilege
# grant silently never took effect (the user ended up with permission=none
# on its own database). The CLI calls the same Scaleway API directly and
# sidesteps both issues.
#
# Re-runs on every deploy (image_tag changes each push): delete-if-exists +
# recreate gives a guaranteed fresh database every time, matching the
# project's existing restore pattern (see scripts/restore_sample_locally.sh,
# restore_prod_locally.sh, restore_prod_to_preprod.sh) of dropping tables
# individually, creating extensions BEFORE restoring, and passing --no-acl
# on both pg_dump and pg_restore so the dump carries no ACL/REVOKE
# statements that could revoke the preview user's own CONNECT privilege.
resource "null_resource" "seed_from_sample" {
  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    environment = {
      INSTANCE_ID       = local.instance_uuid
      DB_NAME           = var.preview_db_name
      DB_USERNAME       = var.preview_db_username
      DB_PASSWORD       = random_password.preview.result
      PREVIEW_DB_URL    = local.preview_db_url
      SAMPLE_DB_URI     = var.sample_db_uri
      EXTENSIONS_SCRIPT = var.create_extensions_script_path
    }
    command = <<-EOT
      set -euo pipefail

      scw rdb database delete instance-id="$INSTANCE_ID" name="$DB_NAME" 2>/dev/null || true
      scw rdb database create instance-id="$INSTANCE_ID" name="$DB_NAME"

      # `user create` on an already-existing name updates it in place
      # (notably resyncs the password to the current Terraform-managed
      # one) rather than erroring, so this is an upsert on every run.
      scw rdb user create instance-id="$INSTANCE_ID" name="$DB_USERNAME" \
        password="$DB_PASSWORD" generate-password=false is-admin=false

      scw rdb privilege set instance-id="$INSTANCE_ID" \
        database-name="$DB_NAME" user-name="$DB_USERNAME" permission=all

      for table in $(psql "$PREVIEW_DB_URL" -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public'"); do
        psql "$PREVIEW_DB_URL" -c "DROP TABLE IF EXISTS \"$table\" CASCADE;"
      done
      psql "$PREVIEW_DB_URL" -f "$EXTENSIONS_SCRIPT"
      pg_dump -Fc --no-acl --no-owner --no-privileges "$SAMPLE_DB_URI" \
        | pg_restore -d "$PREVIEW_DB_URL" \
            --schema=public --clean --no-acl --no-owner --no-privileges \
            --exit-on-error
    EOT
  }

  triggers = {
    image_tag = var.image_tag
  }
}
