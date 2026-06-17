data "scaleway_rdb_instance" "host" {
  instance_id = var.webapp_instance_id
}

resource "random_password" "preview" {
  length  = 32
  special = false
}

resource "scaleway_rdb_database" "preview" {
  instance_id = var.webapp_instance_id
  name        = var.preview_db_name
}

resource "scaleway_rdb_user" "preview" {
  instance_id = var.webapp_instance_id
  name        = var.preview_db_username
  password    = random_password.preview.result
}

resource "scaleway_rdb_privilege" "preview" {
  instance_id   = var.webapp_instance_id
  user_name     = scaleway_rdb_user.preview.name
  database_name = scaleway_rdb_database.preview.name
  permission    = "all"
}

locals {
  host = data.scaleway_rdb_instance.host.load_balancer.0.ip
  port = data.scaleway_rdb_instance.host.load_balancer.0.port

  preview_db_url = format(
    "postgresql://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
    var.preview_db_username,
    random_password.preview.result,
    local.host,
    local.port,
    scaleway_rdb_database.preview.name,
  )
}

# Enable the same extensions as on the sample DB so Django migrations don't fail
# on CREATE EXTENSION statements.
resource "null_resource" "create_extensions" {
  depends_on = [scaleway_rdb_privilege.preview]

  provisioner "local-exec" {
    environment = {
      PGPASSWORD = random_password.preview.result
    }
    command = "psql \"postgresql://${var.preview_db_username}@${local.host}:${local.port}/${var.preview_db_name}?sslmode=require\" -f ${var.create_extensions_script_path}"
  }

  triggers = {
    database_id  = scaleway_rdb_database.preview.id
    user_id      = scaleway_rdb_user.preview.id
    privilege_id = scaleway_rdb_privilege.preview.id
  }
}

# Seed the preview DB from the sample on every deploy (image_tag changes each push).
# Drops and recreates the DB first for a guaranteed clean slate.
resource "null_resource" "seed_from_sample" {
  depends_on = [null_resource.create_extensions]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    # Passwords via env vars: avoids shell expansion of special chars in inline URLs
    environment = {
      PGPASSWORD     = var.admin_password
      PREVIEW_DB_URL = local.preview_db_url
      SAMPLE_DB_URI  = var.sample_db_uri
    }
    command = <<-EOT
      set -euo pipefail
      ADMIN_URL="postgresql://${var.admin_username}@${local.host}:${local.port}/postgres?sslmode=require"
      psql "$ADMIN_URL" -c "DROP DATABASE IF EXISTS ${var.preview_db_name} WITH (FORCE);"
      psql "$ADMIN_URL" -c "CREATE DATABASE ${var.preview_db_name} OWNER ${var.preview_db_username};"
      pg_dump -Fc "$SAMPLE_DB_URI" \
        | pg_restore -d "$PREVIEW_DB_URL" \
            --no-owner --no-privileges \
            --exit-on-error
    EOT
  }

  triggers = {
    image_tag = var.image_tag
  }
}
