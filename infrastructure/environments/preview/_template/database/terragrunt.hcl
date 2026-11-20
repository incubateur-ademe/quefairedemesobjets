# Per-PR preview database, created on the existing preprod RDB instance.
# This directory is materialised to environments/preview/pr-<n>/ by the
# _terragrunt-apply.yml workflow before terragrunt runs; the state key and
# the `environment` input (pr-<n>) derive from the materialised path.
terraform {
  source = "../../../../modules/preview_database"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependency "preprod_database" {
  config_path = "../../../preprod/database"

  mock_outputs = {
    webapp_instance_id   = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    webapp_endpoint_ip   = "10.0.0.1"
    webapp_endpoint_port = 5432
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

# Seed source of a preview, on the same instance.
dependency "preprod_database_sample" {
  config_path = "../../../preprod/database_sample"

  mock_outputs = {
    webapp_db_sample_database_name = "webapp_sample"
    webapp_db_sample_username      = "webapp_sample"
    webapp_db_sample_password      = "mock" # pragma: allowlist secret
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

locals {
  pr_number = get_env("PR_NUMBER")
  image_tag = get_env("IMAGE_TAG")
  clear_db  = get_env("CLEAR_DB", "false") == "true"
  isoprod   = get_env("ISOPROD", "false") == "true"
}

inputs = {
  webapp_instance_id = dependency.preprod_database.outputs.webapp_instance_id

  # Postgres identifiers: underscores, not dashes
  preview_db_name     = "preview_pr_${local.pr_number}"
  preview_db_username = "preview_pr_${local.pr_number}"

  sample_db_uri = format(
    "postgres://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
    dependency.preprod_database_sample.outputs.webapp_db_sample_username,
    dependency.preprod_database_sample.outputs.webapp_db_sample_password,
    dependency.preprod_database.outputs.webapp_endpoint_ip,
    dependency.preprod_database.outputs.webapp_endpoint_port,
    dependency.preprod_database_sample.outputs.webapp_db_sample_database_name,
  )
  image_tag = local.image_tag
  clear_db  = local.clear_db
  isoprod   = local.isoprod

  create_extensions_script_path = abspath("${get_terragrunt_dir()}/../../../../../scripts/sql/create_extensions.sql")
  wagtail_french_script_path    = abspath("${get_terragrunt_dir()}/../../../../../webapp/qfdmd/migrations/sql/create_wagtail_french_config.sql")
}
