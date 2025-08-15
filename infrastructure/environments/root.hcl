generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = ">= 2.55.0"
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
    encrypt                     = true
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

inputs = {
  prefix          = "lvao"
  environment     = "${basename(dirname(get_terragrunt_dir()))}"
  project_id      = "[project_id]"
  organization_id = "[organization_id]"
}