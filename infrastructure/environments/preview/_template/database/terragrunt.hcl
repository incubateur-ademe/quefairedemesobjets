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
    webapp_instance_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    webapp_db_username = "mock_admin"
    webapp_db_password = "mock_password" # pragma: allowlist secret
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

locals {
  pr_number = get_env("PR_NUMBER")
  image_tag = get_env("IMAGE_TAG")
}

inputs = {
  webapp_instance_id = dependency.preprod_database.outputs.webapp_instance_id

  # Postgres identifiers: underscores, not dashes
  preview_db_name     = "preview_pr_${local.pr_number}"
  preview_db_username = "preview_pr_${local.pr_number}"

  admin_username = dependency.preprod_database.outputs.webapp_db_username
  admin_password = dependency.preprod_database.outputs.webapp_db_password

  sample_db_uri = get_env("SAMPLE_DB_URI")
  image_tag     = local.image_tag

  create_extensions_script_path = abspath("${get_terragrunt_dir()}/../../../../../scripts/sql/create_extensions.sql")
}
