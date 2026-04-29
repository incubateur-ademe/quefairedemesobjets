output "container_id" {
  description = "ID du container webapp"
  value       = scaleway_container.webapp.id
}

output "container_name" {
  description = "Nom du container webapp"
  value       = scaleway_container.webapp.name
}

output "domain_name" {
  description = "Domaine interne du container webapp (ex. <container>.functions.fnc.fr-par.scw.cloud), utilisé par nginx comme upstream"
  value       = scaleway_container.webapp.domain_name
}
