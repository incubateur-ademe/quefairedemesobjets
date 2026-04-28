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
    endpoints                   = { s3 = "https://s3.fr-par.scw.cloud" }
    force_path_style            = true
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
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
