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
  zone       = "fr-par-1" # Zone de Paris
  region     = "fr-par"   # Région de Paris
  project_id = var.project_id
}
EOF
}



generate "common_variables" {
  path      = "common_variables.tf"
  if_exists = "overwrite"
  contents  = file("variables.tf")
}

inputs = {
  prefix     = "qfdmod"
}
