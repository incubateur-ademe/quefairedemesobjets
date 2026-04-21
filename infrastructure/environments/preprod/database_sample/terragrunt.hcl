terraform {
  source = "../../../modules/database_sample"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependency "database" {
  config_path = "../database"

  # mock_outputs is used to avoid plan test because the dependency is not yet created
  mock_outputs = {
    webapp_instance_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  instance_id = dependency.database.outputs.webapp_instance_id

  db_name     = "webapp_sample"
  db_username = "[webapp_db_sample_username]"
  db_password = "[webapp_db_sample_password]"

  # Path to the create_extensions.sql script
  # From infrastructure/environments/preprod/database_sample/, we go up 4 levels to the root
  create_extensions_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_extensions.sql")
}
