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

# Carries the image_tag so the database resource below can be forced to
# replace (drop+recreate via the Scaleway API, which has owner permission
# unlike a raw psql DROP/CREATE) on every push.
resource "terraform_data" "image_tag_trigger" {
  input = var.image_tag
}

resource "scaleway_rdb_database" "preview" {
  instance_id = var.webapp_instance_id
  name        = var.preview_db_name

  lifecycle {
    replace_triggered_by = [terraform_data.image_tag_trigger]
  }
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
      PGPASSWORD = var.admin_password
    }
    command = "psql \"postgresql://${var.admin_username}@${local.host}:${local.port}/${var.preview_db_name}?sslmode=require\" -f ${var.create_extensions_script_path}"
  }

  triggers = {
    database_id  = scaleway_rdb_database.preview.id
    user_id      = scaleway_rdb_user.preview.id
    privilege_id = scaleway_rdb_privilege.preview.id
  }
}

# Seed the preview DB from the sample on every deploy. scaleway_rdb_database
# above is replaced (dropped+recreated) on every image_tag change, so this
# always restores into a fresh, empty database.
resource "null_resource" "seed_from_sample" {
  depends_on = [null_resource.create_extensions]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    environment = {
      PREVIEW_DB_URL = local.preview_db_url
      SAMPLE_DB_URI  = var.sample_db_uri
    }
    command = <<-EOT
      set -euo pipefail
      pg_dump -Fc "$SAMPLE_DB_URI" \
        | pg_restore -d "$PREVIEW_DB_URL" \
            --no-owner --no-privileges \
            --exit-on-error
    EOT
  }

  triggers = {
    database_id = scaleway_rdb_database.preview.id
  }
}
