terraform {
  source = "../../../modules/object_storage"
}

include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "env" {
  path = find_in_parent_folders("env.hcl")
}

inputs = {
  # Preview a besoin d'un bucket pour les médias Django (Wagtail uploads)
  # afin de ne pas écrire dans le bucket de prod.
  create_webapp_bucket = true
}
