terraform {
  source = "../../../../modules/webapp_container"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependencies {
  paths = ["../database", "../object_storage"]
}

dependency "preview_database" {
  config_path = "../database"

  mock_outputs = {
    database_url = "postgresql://user:pass@host:5432/db?sslmode=require"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "preview_object_storage" {
  config_path = "../object_storage"

  mock_outputs = {
    bucket_name  = "lvao-preview-mock-media"
    endpoint_url = "https://s3.fr-par.scw.cloud"
    access_key   = "SCWMOCK"
    secret_key   = "MOCKSECRET"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

# The preview container reuses the existing preprod container namespace.
# We pull its ID via a data lookup baked into the module (or pass it in
# explicitly here from a shared output). For simplicity we hard-code the
# preprod namespace ID via env var.
locals {
  commit_sha = get_env("COMMIT_SHA")
  hostname   = "${local.commit_sha}.quefairedemesdechets.incubateur.ademe.dev"
}

remote_state {
  backend = "s3"
  config = {
    bucket                      = "lvao-terraform-state"
    key                         = "preview/${local.commit_sha}/container/terraform.tfstate"
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
  environment  = "preview-${local.commit_sha}"
  namespace_id = get_env("SCALEWAY_PREPROD_NAMESPACE_ID")

  registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:${local.commit_sha}"

  extra_tags = ["preview", "preview-sha-${local.commit_sha}"]

  domain_hostname = local.hostname

  ALLOWED_HOSTS = local.hostname
  DATABASE_URL  = dependency.preview_database.outputs.database_url
  SECRET_KEY    = get_env("PREVIEW_SECRET_KEY")

  AWS_ACCESS_KEY_ID       = dependency.preview_object_storage.outputs.access_key
  AWS_SECRET_ACCESS_KEY   = dependency.preview_object_storage.outputs.secret_key
  AWS_STORAGE_BUCKET_NAME = dependency.preview_object_storage.outputs.bucket_name
  AWS_S3_ENDPOINT_URL     = dependency.preview_object_storage.outputs.endpoint_url
}
