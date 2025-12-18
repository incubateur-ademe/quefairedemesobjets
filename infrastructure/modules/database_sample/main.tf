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
  password    = var.webapp_db_sample_password
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
      psql "postgresql://${var.webapp_db_sample_username}:${var.webapp_db_sample_password}@${data.scaleway_rdb_instance.webapp.load_balancer.0.ip}:${data.scaleway_rdb_instance.webapp.load_balancer.0.port}/${scaleway_rdb_database.webapp_sample.name}?sslmode=require" -f ${var.create_extensions_script_path}
    EOT
  }

  triggers = {
    database_id = scaleway_rdb_database.webapp_sample.id
    user_id     = scaleway_rdb_user.webapp_sample.id
    privilege_id = scaleway_rdb_privilege.webapp_sample_privilege.id
  }
}
