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
  backup_schedule_retention = 30
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

## Webapp Admin User

resource "scaleway_rdb_user" "webapp_admin_user" {
  instance_id = scaleway_rdb_instance.webapp.id
  name        = var.webapp_db_admin_username
  password    = var.webapp_db_admin_password
  is_admin    = true
}

resource "scaleway_rdb_privilege" "webapp_admin_privilege" {
  instance_id   = scaleway_rdb_instance.webapp.id
  user_name     = scaleway_rdb_user.webapp_admin_user.name
  database_name = scaleway_rdb_database.webapp.name
  permission    = "all"
}

## Webapp Metabase User

resource "scaleway_rdb_user" "webapp_metabase_user" {
  instance_id = scaleway_rdb_instance.webapp.id
  name        = var.webapp_db_metabase_username
  password    = var.webapp_db_metabase_password
  is_admin    = false
}

resource "scaleway_rdb_privilege" "webapp_metabase_privilege" {
  instance_id   = scaleway_rdb_instance.webapp.id
  user_name     = scaleway_rdb_user.webapp_metabase_user.name
  database_name = scaleway_rdb_database.webapp.name
  permission    = "readonly"
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

## Warehouse Admin User
resource "scaleway_rdb_user" "warehouse_admin_user" {
  instance_id = scaleway_rdb_instance.warehouse.id
  name        = var.warehouse_db_admin_username
  password    = var.warehouse_db_admin_password
  is_admin    = true
}

resource "scaleway_rdb_privilege" "warehouse_admin_privilege" {
  instance_id   = scaleway_rdb_instance.warehouse.id
  user_name     = scaleway_rdb_user.warehouse_admin_user.name
  database_name = scaleway_rdb_database.warehouse_database.name
  permission    = "all"
}

## Warehouse Metabase User
resource "scaleway_rdb_user" "warehouse_metabase_user" {
  instance_id = scaleway_rdb_instance.warehouse.id
  name        = var.warehouse_db_metabase_username
  password    = var.warehouse_db_metabase_password
  is_admin    = false
}

resource "scaleway_rdb_privilege" "warehouse_metabase_privilege" {
  instance_id   = scaleway_rdb_instance.warehouse.id
  user_name     = scaleway_rdb_user.warehouse_metabase_user.name
  database_name = scaleway_rdb_database.warehouse_database.name
  permission    = "readonly"
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

## Airflow Admin User

resource "scaleway_rdb_user" "airflow_admin_user" {
  instance_id = scaleway_rdb_instance.airflow.id
  name        = var.airflow_db_admin_username
  password    = var.airflow_db_admin_password
  is_admin    = true
}

resource "scaleway_rdb_privilege" "airflow_admin_privilege" {
  instance_id   = scaleway_rdb_instance.airflow.id
  user_name     = scaleway_rdb_user.airflow_admin_user.name
  database_name = scaleway_rdb_database.airflow.name
  permission    = "all"
}

## Cross-DB foreign data wrappers (postgres_fdw) between webapp and warehouse.
## Equivalent to the Django command `manage.py create_remote_db_server`.
## Provisioners are not in state: only a `triggers` change recreates the resource.

locals {
  create_remote_warehouse_in_webapp_script_sha256 = (
    var.create_remote_warehouse_in_webapp_script_path != null
    ? filesha256(var.create_remote_warehouse_in_webapp_script_path)
    : null
  )
  create_remote_webapp_in_warehouse_script_sha256 = (
    var.create_remote_webapp_in_warehouse_script_path != null
    ? filesha256(var.create_remote_webapp_in_warehouse_script_path)
    : null
  )
}

resource "null_resource" "create_remote_warehouse_in_webapp" {
  count = var.create_remote_warehouse_in_webapp_script_path != null ? 1 : 0

  depends_on = [
    scaleway_rdb_database.webapp,
    scaleway_rdb_privilege.webapp_admin_privilege,
    scaleway_rdb_database.warehouse_database,
    scaleway_rdb_privilege.warehouse_admin_privilege,
  ]

  provisioner "local-exec" {
    # Passwords go through env vars: putting them in the URL or inline would
    # let the shell expand `$` characters in passwords (e.g. `N$2$4efJE8c*`).
    environment = {
      PGPASSWORD      = var.webapp_db_admin_password
      REMOTE_PASSWORD = var.warehouse_db_admin_password
    }
    command = <<-EOT
      psql -v ON_ERROR_STOP=1 \
        "postgresql://${var.webapp_db_admin_username}@${scaleway_rdb_instance.webapp.load_balancer.0.ip}:${scaleway_rdb_instance.webapp.load_balancer.0.port}/${scaleway_rdb_database.webapp.name}?sslmode=require" \
        -v warehouse_host='${scaleway_rdb_instance.warehouse.load_balancer.0.ip}' \
        -v warehouse_port='${scaleway_rdb_instance.warehouse.load_balancer.0.port}' \
        -v warehouse_dbname='${scaleway_rdb_database.warehouse_database.name}' \
        -v warehouse_user='${var.warehouse_db_admin_username}' \
        -v warehouse_password="$REMOTE_PASSWORD" \
        -f ${var.create_remote_warehouse_in_webapp_script_path}
    EOT
  }

  triggers = {
    webapp_database_id    = scaleway_rdb_database.webapp.id
    warehouse_database_id = scaleway_rdb_database.warehouse_database.id
    script_sha256         = local.create_remote_warehouse_in_webapp_script_sha256
    local_user            = var.webapp_db_admin_username
    local_user_password   = var.webapp_db_admin_password
    remote_user           = var.warehouse_db_admin_username
    remote_user_password  = var.warehouse_db_admin_password
  }
}

resource "null_resource" "create_remote_webapp_in_warehouse" {
  count = var.create_remote_webapp_in_warehouse_script_path != null ? 1 : 0

  depends_on = [
    scaleway_rdb_database.webapp,
    scaleway_rdb_user.webapp_admin_user,
    scaleway_rdb_privilege.webapp_admin_privilege,
    scaleway_rdb_database.warehouse_database,
    scaleway_rdb_user.warehouse_admin_user,
    scaleway_rdb_privilege.warehouse_admin_privilege,
  ]

  provisioner "local-exec" {
    environment = {
      PGPASSWORD      = var.warehouse_db_admin_password
      REMOTE_PASSWORD = var.webapp_db_admin_password
    }
    command = <<-EOT
      psql -v ON_ERROR_STOP=1 \
        "postgresql://${var.warehouse_db_admin_username}@${scaleway_rdb_instance.warehouse.load_balancer.0.ip}:${scaleway_rdb_instance.warehouse.load_balancer.0.port}/${scaleway_rdb_database.warehouse_database.name}?sslmode=require" \
        -v webapp_host='${scaleway_rdb_instance.webapp.load_balancer.0.ip}' \
        -v webapp_port='${scaleway_rdb_instance.webapp.load_balancer.0.port}' \
        -v webapp_dbname='${scaleway_rdb_database.webapp.name}' \
        -v webapp_user='${var.webapp_db_admin_username}' \
        -v webapp_password="$REMOTE_PASSWORD" \
        -f ${var.create_remote_webapp_in_warehouse_script_path}
    EOT
  }

  triggers = {
    webapp_database_id    = scaleway_rdb_database.webapp.id
    warehouse_database_id = scaleway_rdb_database.warehouse_database.id
    script_sha256         = local.create_remote_webapp_in_warehouse_script_sha256
    local_user            = var.warehouse_db_admin_username
    local_user_password   = var.warehouse_db_admin_password
    remote_user           = var.webapp_db_admin_username
    remote_user_password  = var.webapp_db_admin_password
  }
}
