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

resource "scaleway_object_bucket" "terraform_state" {
  name = "lvao-terraform-state"
  region = "fr-par"
  project_id = var.project_id
}

resource "scaleway_object_bucket_acl" "terraform_state" {
  bucket = scaleway_object_bucket.terraform_state.id
  acl = "private"
}
