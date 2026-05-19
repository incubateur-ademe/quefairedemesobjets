## Web app

resource "scaleway_rdb_instance" "webapp" {
  name                      = "${var.prefix}-${var.environment}-webapp"
  node_type                 = var.webapp_node_type
  engine                    = "PostgreSQL-16"
  is_ha_cluster             = true
  disable_backup            = false
  user_name                 = var.webapp_db_username
  password                  = var.webapp_db_password
  tags                      = ["${var.environment}", "postgresql", "qfdmo"]
  backup_schedule_frequency = 24
  backup_schedule_retention = 7
  backup_same_region        = false
  volume_size_in_gb         = var.webapp_volume_size
  volume_type               = "sbs_15k"
  encryption_at_rest        = true
}

resource "scaleway_rdb_database" "webapp" {
  instance_id = scaleway_rdb_instance.webapp.id
  name        = var.webapp_db_name
}

resource "scaleway_rdb_privilege" "webapp_privilege" {
  instance_id   = scaleway_rdb_instance.webapp.id
  user_name     = var.webapp_db_username
  database_name = scaleway_rdb_database.webapp.name
  permission    = "all"
}

## Warehouse

resource "scaleway_rdb_instance" "warehouse" {
  name                      = "${var.prefix}-${var.environment}-warehouse"
  node_type                 = var.warehouse_node_type
  engine                    = "PostgreSQL-16"
  is_ha_cluster             = true
  disable_backup            = false
  user_name                 = var.warehouse_db_username
  password                  = var.warehouse_db_password
  tags                      = ["${var.environment}", "postgresql", "warehouse", "dbt"]
  backup_schedule_frequency = 24
  backup_schedule_retention = 7
  backup_same_region        = false
  volume_size_in_gb         = var.warehouse_volume_size
  volume_type               = "sbs_15k"
  encryption_at_rest        = true
}

resource "scaleway_rdb_database" "warehouse_database" {
  instance_id = scaleway_rdb_instance.warehouse.id
  name        = var.warehouse_db_name
}

resource "scaleway_rdb_privilege" "warehouse" {
  instance_id   = scaleway_rdb_instance.warehouse.id
  user_name     = var.warehouse_db_username
  database_name = scaleway_rdb_database.warehouse_database.name
  permission    = "all"
}

## Airflow

resource "scaleway_rdb_instance" "airflow" {
  name                      = "${var.prefix}-${var.environment}-airflow"
  node_type                 = var.airflow_node_type
  engine                    = "PostgreSQL-16"
  is_ha_cluster             = true
  disable_backup            = false
  user_name                 = var.airflow_db_username
  password                  = var.airflow_db_password
  tags                      = ["${var.environment}", "postgresql", "airflow", "dbt"]
  backup_schedule_frequency = 24
  backup_schedule_retention = 7
  backup_same_region        = false
  volume_size_in_gb         = var.airflow_volume_size
  volume_type               = "sbs_5k"
  encryption_at_rest        = true
}

resource "scaleway_rdb_database" "airflow" {
  instance_id = scaleway_rdb_instance.airflow.id
  name        = var.airflow_db_name
}

resource "scaleway_rdb_privilege" "airflow" {
  instance_id   = scaleway_rdb_instance.airflow.id
  user_name     = var.airflow_db_username
  database_name = scaleway_rdb_database.airflow.name
  permission    = "all"
}

## Cross-DB foreign data wrappers (postgres_fdw) between webapp and warehouse.
## Equivalent to the Django command `manage.py create_remote_db_server`.

resource "null_resource" "create_remote_warehouse_in_webapp" {
  count = var.create_remote_warehouse_in_webapp_script_path != null ? 1 : 0

  depends_on = [
    scaleway_rdb_database.webapp,
    scaleway_rdb_privilege.webapp_privilege,
    scaleway_rdb_database.warehouse_database,
    scaleway_rdb_privilege.warehouse,
  ]

  provisioner "local-exec" {
    # Passwords go through env vars: putting them in the URL or inline would
    # let the shell expand `$` characters in passwords (e.g. `N$2$4efJE8c*`).
    environment = {
      PGPASSWORD      = var.webapp_db_password
      REMOTE_PASSWORD = var.warehouse_db_password
    }
    command = <<-EOT
      psql "postgresql://${var.webapp_db_username}@${scaleway_rdb_instance.webapp.load_balancer.0.ip}:${scaleway_rdb_instance.webapp.load_balancer.0.port}/${scaleway_rdb_database.webapp.name}?sslmode=require" \
        -v warehouse_host='${scaleway_rdb_instance.warehouse.load_balancer.0.ip}' \
        -v warehouse_port='${scaleway_rdb_instance.warehouse.load_balancer.0.port}' \
        -v warehouse_dbname='${scaleway_rdb_database.warehouse_database.name}' \
        -v warehouse_user='${var.warehouse_db_username}' \
        -v warehouse_password="$REMOTE_PASSWORD" \
        -f ${var.create_remote_warehouse_in_webapp_script_path}
    EOT
  }

  triggers = {
    webapp_database_id    = scaleway_rdb_database.webapp.id
    warehouse_database_id = scaleway_rdb_database.warehouse_database.id
    script_path           = var.create_remote_warehouse_in_webapp_script_path
  }
}

resource "null_resource" "create_remote_webapp_in_warehouse" {
  count = var.create_remote_webapp_in_warehouse_script_path != null ? 1 : 0

  depends_on = [
    scaleway_rdb_database.webapp,
    scaleway_rdb_privilege.webapp_privilege,
    scaleway_rdb_database.warehouse_database,
    scaleway_rdb_privilege.warehouse,
  ]

  provisioner "local-exec" {
    environment = {
      PGPASSWORD      = var.warehouse_db_password
      REMOTE_PASSWORD = var.webapp_db_password
    }
    command = <<-EOT
      psql "postgresql://${var.warehouse_db_username}@${scaleway_rdb_instance.warehouse.load_balancer.0.ip}:${scaleway_rdb_instance.warehouse.load_balancer.0.port}/${scaleway_rdb_database.warehouse_database.name}?sslmode=require" \
        -v webapp_host='${scaleway_rdb_instance.webapp.load_balancer.0.ip}' \
        -v webapp_port='${scaleway_rdb_instance.webapp.load_balancer.0.port}' \
        -v webapp_dbname='${scaleway_rdb_database.webapp.name}' \
        -v webapp_user='${var.webapp_db_username}' \
        -v webapp_password="$REMOTE_PASSWORD" \
        -f ${var.create_remote_webapp_in_warehouse_script_path}
    EOT
  }

  triggers = {
    webapp_database_id    = scaleway_rdb_database.webapp.id
    warehouse_database_id = scaleway_rdb_database.warehouse_database.id
    script_path           = var.create_remote_webapp_in_warehouse_script_path
  }
}
