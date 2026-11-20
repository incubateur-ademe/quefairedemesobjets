# Per-PR webapp container, deployed in the shared qfdmod-preview namespace.
# Materialised to environments/preview/pr-<n>/ by the _terragrunt-apply.yml
# workflow; `environment` (pr-<n>) and the state key derive from the
# materialised path.
include "root" {
  path = find_in_parent_folders("root.hcl")
}

# The same description as preprod and prod, fed by ../../env.hcl and by the
# ../database unit. deep: the inputs below are added to the shared ones and
# win over them.
include "stack" {
  path           = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/webapp_container.hcl"
  merge_strategy = "deep"
}

# One directory deeper than preprod and prod.
terraform {
  source = "../../../../modules/webapp_container"
}

dependencies {
  paths = ["../object_storage"]
}

dependency "preview_namespace" {
  config_path = "../../namespace"

  mock_outputs = {
    namespace_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "preview_object_storage" {
  config_path = "../object_storage"

  mock_outputs = {
    bucket_name = "lvao-preview-mock-media"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

locals {
  pr_number = get_env("PR_NUMBER")
  # preview:isoprod label: a preview meant to be used like production
  # (beta tests), see the database unit for its data.
  isoprod = get_env("ISOPROD", "false") == "true"
}

inputs = {
  namespace_id = dependency.preview_namespace.outputs.namespace_id

  # preview-isoprod marks the container of an isoprod preview.
  extra_tags = concat(
    ["preview", "preview-pr-${local.pr_number}"],
    local.isoprod ? ["preview-isoprod"] : [],
  )

  # Always on and twice the CPU for an isoprod preview: testers must not
  # hit a cold start, and the full database is heavier to serve.
  min_scale = local.isoprod ? 1 : 0
  cpu_limit = local.isoprod ? 2000 : 1000

  # The contact form of preprod.
  NOTION_CONTACT_FORM_DATABASE_ID = "17c6523d57d7808b8cc5f5ccae264f7c"

  # reuses the project-wide Scaleway key (no IAM write access to
  # mint a bucket-scoped one). Revisit if IAM permissions are granted.
  AWS_ACCESS_KEY_ID       = get_env("SCW_ACCESS_KEY")
  AWS_SECRET_ACCESS_KEY   = get_env("SCW_SECRET_KEY")
  AWS_STORAGE_BUCKET_NAME = dependency.preview_object_storage.outputs.bucket_name

  extra_environment_variables = {
    # Its Scaleway address has no nginx in front: noindex by meta tag, the
    # gateway adds X-Robots-Tag.
    BLOCK_ROBOTS = "true"
  }

  worker_enabled = false
  # Persistent connections would add up across previews on the shared
  # preprod instance.
  CONN_MAX_AGE = 0

  # Keep the container warm for 1h after the last request to avoid cold starts.
  timeout = 3600
}
