output "webapp_sample_database_name" {
  description = "Nom de la base de données sample webapp"
  value       = var.webapp_db_sample_name != null && var.webapp_db_sample_name != "" ? scaleway_rdb_database.webapp_sample[0].name : null
}

output "webapp_sample_username" {
  description = "Nom d'utilisateur de la base de données sample webapp"
  value       = var.webapp_db_sample_name != null && var.webapp_db_sample_name != "" ? var.webapp_db_sample_username : null
}

