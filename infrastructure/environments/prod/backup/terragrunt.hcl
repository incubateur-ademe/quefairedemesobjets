terraform {
  source = "../../../modules/backup"
}

dependency "database" {
  config_path = "../database"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    webapp_instance_id     = "fr-par/mock-webapp-id"
    webapp_database_name   = "webapp"
    airflow_instance_id    = "fr-par/mock-warehouse-id"
    airflow_database_name  = "airflow"
    metabase_instance_id   = "fr-par/mock-warehouse-id"
    metabase_database_name = "metabase"
  }
}

dependency "object_storage" {
  config_path = "../object_storage"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    versioned_bucket_names = ["mock-bucket"]
  }
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  # The warehouse database is not dumped: dbt rebuilds it from the webapp
  # database and the sources.
  databases = [
    {
      instance_id = dependency.database.outputs.webapp_instance_id
      name        = dependency.database.outputs.webapp_database_name
    },
    {
      instance_id = dependency.database.outputs.airflow_instance_id
      name        = dependency.database.outputs.airflow_database_name
    },
    {
      instance_id = dependency.database.outputs.metabase_instance_id
      name        = dependency.database.outputs.metabase_database_name
    },
  ]

  buckets = dependency.object_storage.outputs.versioned_bucket_names
}
