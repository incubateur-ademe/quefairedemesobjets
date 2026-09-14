terraform {
  source = "../../../modules/metabase_containers"
}

dependency "database" {
  config_path = "../database"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    metabase_instance_id   = "mock-metabase-id"
    metabase_database_name = "metabase"
    metabase_endpoint_ip   = "127.0.0.1"
    metabase_endpoint_port = 5432
    metabase_db_username   = "mock_metabase"
    metabase_db_password   = "mock_password" # pragma: allowlist secret
  }
}

dependencies {
  paths = ["../database"]
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  # Override the project-wide "lvao" prefix for this stack only.
  prefix = "qfdmod"

  metabase_registry_image = "metabase/metabase"
  tag_docker              = "[tag_docker]"
  metabase_cpu_limit      = 1000
  metabase_memory_limit   = 2048
  metabase_min_scale      = 1
  metabase_max_scale      = 1
  metabase_timeout        = 300

  MB_SITE_NAME             = "LVAO preprod"
  MB_ENCRYPTION_SECRET_KEY = "[MB_ENCRYPTION_SECRET_KEY]"
  MB_DB_CONNECTION_URI     = "postgres://${dependency.database.outputs.metabase_db_username}:${dependency.database.outputs.metabase_db_password}@${dependency.database.outputs.metabase_endpoint_ip}:${dependency.database.outputs.metabase_endpoint_port}/${dependency.database.outputs.metabase_database_name}?sslmode=require"
}
