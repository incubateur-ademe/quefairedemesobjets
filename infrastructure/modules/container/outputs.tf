output "namespace_id" {
  description = "ID du namespace de containers Scaleway (réutilisable par d'autres containers comme webapp/nginx)"
  value       = scaleway_container_namespace.main.id
}

output "namespace_name" {
  description = "Nom du namespace de containers Scaleway"
  value       = scaleway_container_namespace.main.name
}
