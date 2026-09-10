output "container_id" {
  description = "ID du container Metabase"
  value       = scaleway_container.metabase.id
}

output "domain_name" {
  description = "Nom de domaine public Scaleway du container Metabase"
  value       = scaleway_container.metabase.domain_name
}

output "public_endpoint" {
  description = "URL publique du container Metabase"
  value       = "https://${scaleway_container.metabase.domain_name}"
}
