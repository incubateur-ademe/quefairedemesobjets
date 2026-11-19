# What the `database` stack is in every environment. An environment's
# terragrunt.hcl includes this file and adds what is its own.
terraform {
  source = "${get_terragrunt_dir()}/../../../modules/database"
}

inputs = {
  # Web app
  webapp_db_name              = "webapp"
  webapp_db_username          = "webapp"
  webapp_db_metabase_username = "webapp_metabase"

  # Warehouse
  warehouse_db_name              = "warehouse"
  warehouse_db_username          = "warehouse"
  warehouse_db_metabase_username = "warehouse_metabase"

  # Airflow (database on warehouse instance)
  airflow_db_name     = "airflow"
  airflow_db_username = "airflow"

  # Default privileges of the read-only Metabase users
  grant_metabase_default_privileges_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/grant_metabase_default_privileges.sql")
}
