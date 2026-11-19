data "scaleway_rdb_instance" "webapp" {
  instance_id = var.webapp_instance_id
}

resource "scaleway_rdb_database" "webapp_sample" {
  instance_id = var.webapp_instance_id
  name        = var.webapp_db_sample_name
}

resource "scaleway_rdb_user" "webapp_sample" {
  instance_id = var.webapp_instance_id
  name        = var.webapp_db_sample_username
  password    = random_password.db.result
}

resource "scaleway_rdb_privilege" "webapp_sample_privilege" {
  instance_id   = var.webapp_instance_id
  user_name     = var.webapp_db_sample_username
  database_name = scaleway_rdb_database.webapp_sample.name
  permission    = "all"
}

resource "null_resource" "create_extensions" {
  depends_on = [
    scaleway_rdb_database.webapp_sample,
    scaleway_rdb_user.webapp_sample,
    scaleway_rdb_privilege.webapp_sample_privilege
  ]

  provisioner "local-exec" {
    command = <<-EOT
      psql "postgresql://${var.webapp_db_sample_username}:${random_password.db.result}@${data.scaleway_rdb_instance.webapp.load_balancer.0.ip}:${data.scaleway_rdb_instance.webapp.load_balancer.0.port}/${scaleway_rdb_database.webapp_sample.name}?sslmode=require" -f ${var.create_extensions_script_path}
    EOT
  }

  triggers = {
    database_id  = scaleway_rdb_database.webapp_sample.id
    user_id      = scaleway_rdb_user.webapp_sample.id
    privilege_id = scaleway_rdb_privilege.webapp_sample_privilege.id
  }
}

# The password of the sample user is generated here, never typed.
# Rotate it with: tofu apply -replace='random_password.db'
resource "random_password" "db" {
  length  = 32
  special = true
  # Scaleway RDB requires at least one special char, digit, lowercase and
  # uppercase letter. Restricted to chars that don't need URL-encoding in a
  # postgres:// DSN (no @, :, /, ?, #, %).
  override_special = "-_.~!*"
  min_special      = 1
  min_numeric      = 1
  min_lower        = 1
  min_upper        = 1

  # A password adopted from before keeps its own shape
  lifecycle {
    ignore_changes = all
  }
}

# The password typed before it was generated here: while the stack secret
# still holds it, it is imported so that nothing rotates. OpenTofu shows an
# import id in the plan: it appears once, in the output of that apply.
# To delete, with the variable, once every environment is applied.
import {
  for_each = nonsensitive(var.webapp_db_sample_password != null) ? toset(["adopted"]) : toset([])
  to       = random_password.db
  id       = nonsensitive(var.webapp_db_sample_password)
}
