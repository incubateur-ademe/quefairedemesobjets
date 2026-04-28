terraform {
  source = "../../../../modules/preview_database"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependency "preprod_database" {
  config_path = "../../../preprod/database"

  mock_outputs = {
    webapp_instance_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

locals {
  commit_sha = get_env("COMMIT_SHA")
}

# Each preview gets isolated state under preview/<sha>/database in the
# shared lvao-terraform-state bucket. Override the auto-generated key so it
# doesn't include the literal "_template" path segment.
remote_state {
  backend = "s3"
  config = {
    bucket                      = "lvao-terraform-state"
    key                         = "preview/${local.commit_sha}/database/terraform.tfstate"
    region                      = "fr-par"
    endpoint                    = "s3.fr-par.scw.cloud"
    skip_credentials_validation = true
    skip_region_validation      = true
    encrypt                     = false
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
}

inputs = {
  webapp_instance_id = dependency.preprod_database.outputs.webapp_instance_id

  preview_db_name     = "preview_${local.commit_sha}"
  preview_db_username = "preview_${local.commit_sha}"

  sample_db_uri = get_env("SAMPLE_DB_URI")

  create_extensions_script_path = abspath("${get_terragrunt_dir()}/../../../../../scripts/sql/create_extensions.sql")
}
