terraform {
  source = "../../../modules/database_sample"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependency "database" {
  config_path = "../database"

  mock_outputs = {
    webapp_instance_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  webapp_instance_id = dependency.database.outputs.webapp_instance_id

  webapp_db_sample_name     = "webapp_sample"  # Optionnel, mettre null ou "" pour désactiver
  webapp_db_sample_username = "[webapp_db_sample_username]"
  webapp_db_sample_password = "[webapp_db_sample_password]"
}

