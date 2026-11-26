locals {
  environment = basename(dirname(get_terragrunt_dir()))
  stack       = basename(get_terragrunt_dir())

  # A stack that ships a secrets.example.json takes the inputs listed there
  # from Scaleway Secret Manager: secret <stack> at path /terraform/<environment>,
  # a JSON object written by `make -C infrastructure secrets-push`.
  secrets = jsondecode(run_cmd(
    "--terragrunt-quiet",
    "${get_parent_terragrunt_dir()}/../../scripts/infrastructure/stack_secrets.sh",
    local.environment, local.stack,
  ))
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = ">= 2.78.0"
    }
  }
}

provider "scaleway" {
  zone   = "fr-par-1" # Zone de Paris
  region = "fr-par"   # Région de Paris
}
EOF
}

generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  backend "s3" {
    endpoint                    = "s3.fr-par.scw.cloud"
    bucket                      = "lvao-terraform-state"
    key                         = "${path_relative_to_include()}/terraform.tfstate"
    region                      = "fr-par"
    skip_credentials_validation = true
    skip_region_validation      = true
    encrypt                     = false
    access_key                  = var.access_key
    secret_key                  = var.secret_key
  }
}
EOF
}

generate "common_variables" {
  path      = "common_variables.tf"
  if_exists = "overwrite"
  contents  = file("variables.tf")
}

# The Scaleway credentials come from the SCW_* environment variables, like the
# provider's. A stack's own inputs win over its secret.
inputs = merge(
  {
    prefix          = "lvao"
    environment     = local.environment
    access_key      = get_env("SCW_ACCESS_KEY", "")
    secret_key      = get_env("SCW_SECRET_KEY", "")
    project_id      = get_env("SCW_DEFAULT_PROJECT_ID", "")
    organization_id = get_env("SCW_DEFAULT_ORGANIZATION_ID", "")
  },
  local.secrets,
)
