## Webapp sample

output "webapp_db_sample_database_name" {
  description = "Nom de la base de données webapp"
  value       = scaleway_rdb_database.webapp_sample.name
}

output "webapp_db_sample_username" {
  description = "Nom d'utilisateur de la base de données webapp"
  value       = var.webapp_db_sample_username
}

output "webapp_db_sample_password" {
  description = "Mot de passe de la base de données webapp"
  value       = var.webapp_db_sample_password
  sensitive   = true
}
