#

terraform {
  backend "s3" {
    endpoint                    = "s3.fr-par.scw.cloud"
    bucket                      = "${var.prefix}-terraformstate-${var.environment}"
    key                         = "terraform.tfstate"
    region                      = "fr-par"
    skip_credentials_validation = true
    skip_region_validation      = true
    encrypt                     = false
    access_key                  = var.access_key
    secret_key                  = var.secret_key
  }
}
