output "webapp_instance_id" {
  description = "ID de l'instance RDB webapp"
  value       = scaleway_rdb_instance.webapp.id
}

output "webapp_database_name" {
  description = "Nom de la base de données webapp"
  value       = scaleway_rdb_database.webapp.name
}

output "webapp_database_url" {
  description = "DSN postgres complet vers la base webapp (utilisé par Django comme DATABASE_URL)"
  value       = "postgres://${var.webapp_db_username}:${var.webapp_db_password}@${scaleway_rdb_instance.webapp.load_balancer[0].ip}:${scaleway_rdb_instance.webapp.load_balancer[0].port}/${scaleway_rdb_database.webapp.name}?sslmode=require"
  sensitive   = true
}

output "warehouse_database_url" {
  description = "DSN postgres complet vers la base warehouse (utilisé par Django comme DB_WAREHOUSE)"
  value       = "postgres://${var.warehouse_db_username}:${var.warehouse_db_password}@${scaleway_rdb_instance.warehouse.load_balancer[0].ip}:${scaleway_rdb_instance.warehouse.load_balancer[0].port}/${scaleway_rdb_database.warehouse_database.name}?sslmode=require"
  sensitive   = true
}

