output "container_id" {
  value = scaleway_container.webapp.id
}

output "public_endpoint" {
  description = "Endpoint public auto-généré par Scaleway pour le container"
  value       = scaleway_container.webapp.public_endpoint
}

output "worker_container_id" {
  value = one(scaleway_container.worker[*].id)
}

output "registry_image" {
  description = "Image running now: pass its tag as IMAGE_TAG to apply by hand without redeploying"
  value       = scaleway_container.webapp.registry_image
}
