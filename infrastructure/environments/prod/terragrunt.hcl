terraform {
  source = "../../modules/database"
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  node_type         = "DB-PRO2-XXS"
  volume_size       = 300
  db_username       = "[db_username]"
  db_password       = "[db_password]"
  db_name           = "qfdmo"
  warehouse_db_name = "warehouse"
}