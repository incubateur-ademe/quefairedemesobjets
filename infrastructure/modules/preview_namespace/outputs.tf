output "namespace_id" {
  description = "ID du namespace Scaleway Container partagé par les previews"
  value       = scaleway_container_namespace.preview.id
}
