resource "scaleway_object_bucket" "terraform_state" {
  name = "lvao-terraform-state"
  region = "fr-par"
  project_id = var.project_id
}

resource "scaleway_object_bucket_acl" "terraform_state" {
  bucket = scaleway_object_bucket.terraform_state.id
  acl = "private"
}
