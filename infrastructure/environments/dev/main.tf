module "provider" {
  source = "../../modules/provider"
}

module "database" {
  source = "../../modules/database"

  environment = var.environment
  node_type   = "DB-DEV-S"
  volume_size = 100
  db_password = var.db_password
  project_id = var.project_id
  organization_id = var.organization_id
}
