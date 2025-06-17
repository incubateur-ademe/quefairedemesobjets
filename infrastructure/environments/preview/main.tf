### Providers ###

terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = ">= 2.55.0"
    }
  }
}

provider "scaleway" {
  zone   = "fr-par-1"
  region = "fr-par"
}

### Modules ###

module "database" {
  source = "../../modules/database"

  prefix      = var.prefix
  environment = var.environment
  tags        = var.tags
  node_type   = "DB-DEV-S"
  volume_size = 100
  db_username = var.db_username
  db_password = var.db_password
  db_name     = var.db_name
  project_id = var.project_id
  organization_id = var.organization_id
}
