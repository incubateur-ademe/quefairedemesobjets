# What the `database_sample` stack is in every environment. An environment's
# terragrunt.hcl includes this file and adds what is its own.
terraform {
  source = "${get_terragrunt_dir()}/../../../modules/database_sample"
}

dependency "database" {
  config_path = "${get_terragrunt_dir()}/../database"

  # mock_outputs is used to avoid plan test because the dependency is not yet created
  mock_outputs = {
    webapp_instance_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  webapp_instance_id = dependency.database.outputs.webapp_instance_id

  webapp_db_sample_name     = "webapp_sample"
  webapp_db_sample_username = "webapp_sample"

  # Path to the create_extensions.sql script
  create_extensions_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_extensions.sql")
}
