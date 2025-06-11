module "provider" {
  source = "../../modules/provider"
}

module "backend" {
  source = "../../modules/backend"
  project_id = var.project_id
}
