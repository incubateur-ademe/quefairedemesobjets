output "webapp_sample_database_url" {
  description = "DSN postgres complet vers la base sample (utilisé par Django comme DB_WEBAPP_SAMPLE)"
  value       = "postgres://${var.webapp_db_sample_username}:${var.webapp_db_sample_password}@${data.scaleway_rdb_instance.webapp.load_balancer[0].ip}:${data.scaleway_rdb_instance.webapp.load_balancer[0].port}/${scaleway_rdb_database.webapp_sample.name}?sslmode=require"
  sensitive   = true
}
