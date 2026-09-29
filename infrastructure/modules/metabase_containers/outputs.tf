output "container_id" {
  description = "ID du container Metabase"
  value       = scaleway_container.metabase.id
}

output "domain_name" {
  description = "Nom de domaine public Scaleway du container Metabase (upstream du gateway nginx)"
  value       = scaleway_container.metabase.domain_name
}

output "custom_domain" {
  description = "Hostname public de Metabase via le gateway nginx, s'il est configuré"
  value       = local.custom_domain_enabled ? var.custom_domain : null
}

output "public_endpoint" {
  description = "URL publique du container Metabase"
  value = local.custom_domain_enabled ? (
    "https://${var.custom_domain}"
  ) : "https://${scaleway_container.metabase.domain_name}"
}
