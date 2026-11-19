terraform {
  source = "../../../modules/database"
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  # Web app
  webapp_node_type            = "DB-PRO2-XXS"
  webapp_db_name              = "webapp"
  webapp_db_username          = "webapp"
  webapp_db_metabase_username = "webapp_metabase"
  webapp_volume_size          = 20

  # Warehouse
  warehouse_node_type            = "DB-PRO2-XXS"
  warehouse_db_name              = "warehouse"
  warehouse_db_username          = "warehouse"
  warehouse_db_metabase_username = "warehouse_metabase"
  warehouse_volume_size          = 100

  # Airflow (database on warehouse instance)
  airflow_db_name     = "airflow"
  airflow_db_username = "airflow"

  # Metabase (database on warehouse instance)
  metabase_db_username = "metabase"

  # DEPRECATED
  airflow_node_type   = "DB-PLAY2-NANO"
  airflow_volume_size = 20

  # Cross-DB postgres_fdw setup between webapp and warehouse.
  # From infrastructure/environments/airflowv3/database/, go up 4 levels to repo root.
  # create_remote_warehouse_in_webapp_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_remote_warehouse_in_webapp.sql")
  # create_remote_webapp_in_warehouse_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_remote_webapp_in_warehouse.sql")

  # Default privileges of the read-only Metabase users
  grant_metabase_default_privileges_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/grant_metabase_default_privileges.sql")
}