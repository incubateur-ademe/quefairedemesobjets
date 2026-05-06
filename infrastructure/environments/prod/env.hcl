generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  backend "s3" {
    endpoint                    = "s3.fr-par.scw.cloud"
    bucket                      = "qfdmod-terraform-state-prod"
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

inputs = {
  environment = "prod"
}
