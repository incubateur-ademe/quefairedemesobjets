### Backend ###

# S3 bucket for storing Terraform state
# This is used to store the state of the Terraform configuration
# for the production environment

terraform {
  backend "s3" {
    endpoint                    = "s3.fr-par.scw.cloud"
    bucket                     = "${var.prefix}-terraform-state"
    key                        = "${var.environment}/terraform.tfstate"
    region                     = "fr-par"
    skip_credentials_validation = true
    skip_region_validation     = true
    encrypt                    = true
    access_key                 = var.access_key
    secret_key                 = var.secret_key
  }
}