terraform {
  source = "../../../../modules/preview_object_storage"
}

include {
  path = find_in_parent_folders("root.hcl")
}

locals {
  commit_sha = get_env("COMMIT_SHA")
}

remote_state {
  backend = "s3"
  config = {
    bucket                      = "lvao-terraform-state"
    key                         = "preview/${local.commit_sha}/object_storage/terraform.tfstate"
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
  environment            = "preview-${local.commit_sha}"
  object_expiration_days = 1
}
