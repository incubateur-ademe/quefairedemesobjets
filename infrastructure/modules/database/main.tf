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
  database_name = scaleway_rdb_database.warehouse.name
  permission    = "all"
}
