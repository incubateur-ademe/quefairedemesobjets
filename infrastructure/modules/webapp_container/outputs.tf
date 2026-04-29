output "container_id" {
  value = scaleway_container.webapp.id
}

output "container_domain_name" {
  description = "Domaine auto-généré par Scaleway (avant attache du custom domain)"
  value       = scaleway_container.webapp.domain_name
}

output "custom_hostname" {
  description = "Hostname custom attaché (si fourni)"
  value       = var.domain_hostname == "" ? null : var.domain_hostname
}
