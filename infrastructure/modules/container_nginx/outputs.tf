output "container_id" {
  description = "ID du container nginx"
  value       = scaleway_container.nginx.id
}

output "domain_name" {
  description = "Domaine public du container nginx (point d'entrée HTTPS de l'environnement)"
  value       = scaleway_container.nginx.domain_name
}
