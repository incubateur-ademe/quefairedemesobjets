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

### Modules ###

module "backend" {
  source = "../../modules/backend"
  project_id = var.project_id
}
