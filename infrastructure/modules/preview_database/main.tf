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
    "postgresql://%s:%s@%s:%s/%s?sslmode=require",
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
    command = "psql \"${local.preview_db_url}\" -f ${var.create_extensions_script_path}"
  }

  triggers = {
    database_id  = scaleway_rdb_database.preview.id
    user_id      = scaleway_rdb_user.preview.id
    privilege_id = scaleway_rdb_privilege.preview.id
  }
}

# Seed the preview DB by piping pg_dump (from the sample) into pg_restore
# (into the preview). Mirrors the .github/actions/prepare-django-db pattern.
resource "null_resource" "seed_from_sample" {
  depends_on = [null_resource.create_extensions]

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      pg_dump -Fc "${var.sample_db_uri}" \
        | pg_restore -d "${local.preview_db_url}" \
            --clean --if-exists --no-owner --no-privileges \
            --exit-on-error
    EOT
  }

  triggers = {
    database_id = scaleway_rdb_database.preview.id
  }
}
