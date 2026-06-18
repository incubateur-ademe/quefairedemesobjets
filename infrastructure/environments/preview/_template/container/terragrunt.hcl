# Per-PR webapp container, deployed in the shared lvao-preview namespace.
# Materialised to environments/preview/pr-<n>/ by the _terragrunt-apply.yml
# workflow; `environment` (pr-<n>) and the state key derive from the
# materialised path.
terraform {
  source = "../../../../modules/webapp_container"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependencies {
  paths = ["../database", "../object_storage"]
}

dependency "preview_namespace" {
  config_path = "../../namespace"

  mock_outputs = {
    namespace_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "preview_database" {
  config_path = "../database"

  mock_outputs = {
    database_url = "postgresql://user:pass@host:5432/db?sslmode=require" # pragma: allowlist secret
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "preview_object_storage" {
  config_path = "../object_storage"

  mock_outputs = {
    bucket_name  = "lvao-preview-mock-media"
    endpoint_url = "https://s3.fr-par.scw.cloud"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

locals {
  pr_number = get_env("PR_NUMBER")
  # Tag set by preview-up.yml: pr-<n>-<shortsha>. Including the SHA forces a
  # container redeploy on every push (the image reference changes).
  image_tag = get_env("IMAGE_TAG")
}

inputs = {
  namespace_id   = dependency.preview_namespace.outputs.namespace_id
  registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:${local.image_tag}"

  extra_tags = ["preview", "preview-pr-${local.pr_number}"]

  # The container is served on its Scaleway-generated domain, unknown before
  # apply: trust the whole generated-domain suffix (Django wildcard syntax).
  ALLOWED_HOSTS = ".functions.fnc.fr-par.scw.cloud"

  DATABASE_URL = dependency.preview_database.outputs.database_url
  SECRET_KEY   = get_env("PREVIEW_SECRET_KEY")

  # ponytail: reuses the project-wide Scaleway key (no IAM write access to
  # mint a bucket-scoped one). Revisit if IAM permissions are granted.
  AWS_ACCESS_KEY_ID       = get_env("SCW_ACCESS_KEY")
  AWS_SECRET_ACCESS_KEY   = get_env("SCW_SECRET_KEY")
  AWS_STORAGE_BUCKET_NAME = dependency.preview_object_storage.outputs.bucket_name
  AWS_S3_ENDPOINT_URL     = dependency.preview_object_storage.outputs.endpoint_url
}
