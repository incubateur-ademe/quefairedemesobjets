### Resources DB ###

resource "scaleway_rdb_instance" "main" {
  name                      = "${var.prefix}-${var.environment}-db"
  node_type                 = var.node_type
  engine                    = "PostgreSQL-16"
  is_ha_cluster             = true
  disable_backup            = false
  user_name                 = var.db_username
  password                  = var.db_password
  tags                      = ["${var.environment}", "postgresql", "qfdmo", "warehouse", "dbt"]
  backup_schedule_frequency = 24
  backup_schedule_retention = 7
  backup_same_region        = false
  volume_size_in_gb         = var.volume_size
  volume_type               = "sbs_15k"
  encryption_at_rest        = true
}

resource "scaleway_rdb_database" "main" {
  instance_id = scaleway_rdb_instance.main.id
  name        = var.db_name
}

resource "scaleway_rdb_privilege" "main_privilege" {
  instance_id   = scaleway_rdb_instance.main.id
  user_name     = var.db_username
  database_name = scaleway_rdb_database.main.name
  permission    = "all"
}

resource "scaleway_rdb_database" "warehouse" {
  instance_id = scaleway_rdb_instance.main.id
  name        = var.warehouse_db_name
}

resource "scaleway_rdb_privilege" "warehouse_privilege" {
  instance_id   = scaleway_rdb_instance.main.id
  user_name     = var.db_username
  database_name = scaleway_rdb_database.warehouse.name
  permission    = "all"
}
