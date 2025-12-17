output "webapp_instance_id" {
  description = "ID de l'instance RDB webapp"
  value       = scaleway_rdb_instance.webapp.id
}

output "webapp_database_name" {
  description = "Nom de la base de données webapp"
  value       = scaleway_rdb_database.webapp.name
}

