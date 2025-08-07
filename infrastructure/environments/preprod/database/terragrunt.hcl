terraform {
  source = "../../../modules/database"
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  # Web app
  webapp_node_type   = "DB-PLAY2-NANO"
  webapp_db_name     = "webapp"
  webapp_db_username = "[webapp_db_username]"
  webapp_db_password = "[webapp_db_password]"
  webapp_volume_size = 20

  # Warehouse
  warehouse_node_type   = "DB-PLAY2-NANO"
  warehouse_db_name     = "warehouse"
  warehouse_db_username = "[warehouse_db_username]"
  warehouse_db_password = "[warehouse_db_password]"
  warehouse_volume_size = 100
}