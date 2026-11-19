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
  webapp_volume_size = 20

  # Warehouse
  warehouse_node_type   = "DB-PLAY2-NANO"
  warehouse_db_name     = "warehouse"
  warehouse_volume_size = 100

  # Airflow (database on warehouse instance)
  airflow_db_name = "airflow"
  # Cross-DB postgres_fdw setup between webapp and warehouse.
  create_remote_warehouse_in_webapp_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_remote_warehouse_in_webapp.sql")
  create_remote_webapp_in_warehouse_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_remote_webapp_in_warehouse.sql")
  grant_metabase_default_privileges_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/grant_metabase_default_privileges.sql")
}