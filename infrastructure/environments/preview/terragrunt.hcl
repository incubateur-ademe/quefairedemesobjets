terraform {
  source = "../../modules/database"
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  node_type         = "DB-DEV-S"
  volume_size       = 100
  db_username       = "[db_username]"
  db_password       = "[db_password]"
  db_name           = "qfdmo"
  warehouse_db_name = "warehouse"
}
