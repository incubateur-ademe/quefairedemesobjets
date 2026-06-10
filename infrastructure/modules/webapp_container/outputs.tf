output "container_id" {
  value = scaleway_container.webapp.id
}

output "public_endpoint" {
  description = "Endpoint public auto-généré par Scaleway pour le container"
  value       = scaleway_container.webapp.public_endpoint
}
