data "scaleway_rdb_instance" "instance" {
  instance_id = var.instance_id
}

resource "scaleway_rdb_database" "addeddb" {
  instance_id = var.instance_id
  name        = var.db_name
}

resource "scaleway_rdb_user" "addeddb" {
  instance_id = var.instance_id
  name        = var.db_username
  password    = var.db_password
}

resource "scaleway_rdb_privilege" "addeddb_privilege" {
  instance_id   = var.instance_id
  user_name     = var.db_username
  database_name = scaleway_rdb_database.addeddb.name
  permission    = "all"
}

resource "null_resource" "create_extensions" {
  depends_on = [
    scaleway_rdb_database.addeddb,
    scaleway_rdb_user.addeddb,
    scaleway_rdb_privilege.addeddb_privilege
  ]

  provisioner "local-exec" {
    command = <<-EOT
      psql "postgresql://${var.db_username}:${var.db_password}@${data.scaleway_rdb_instance.instance.load_balancer.0.ip}:${data.scaleway_rdb_instance.instance.load_balancer.0.port}/${scaleway_rdb_database.addeddb.name}?sslmode=require" -f ${var.create_extensions_script_path}
    EOT
  }

  triggers = {
    database_id  = scaleway_rdb_database.addeddb.id
    user_id      = scaleway_rdb_user.addeddb.id
    privilege_id = scaleway_rdb_privilege.addeddb_privilege.id
  }
}
