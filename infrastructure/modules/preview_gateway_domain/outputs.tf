output "url" {
  description = "https://pr-<n>.<domain>, empty without a domain"
  value       = var.domain == "" ? "" : "https://${scaleway_container_domain.preview[0].hostname}"
}
