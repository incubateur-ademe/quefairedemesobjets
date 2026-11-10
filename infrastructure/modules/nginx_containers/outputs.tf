output "container_id" {
  description = "ID du container nginx gateway"
  value       = scaleway_container.nginx.id
}

output "domain_name" {
  description = "Nom de domaine public Scaleway du gateway (cible des CNAME wildcard)"
  value       = scaleway_container.nginx.domain_name
}

output "hostnames" {
  description = "Hostnames publics attachés au gateway"
  value       = [for route in var.routes : route.hostname]
}

output "public_endpoints" {
  description = "URL publiques routées par le gateway"
  value = {
    for name, route in var.routes :
    name => "https://${route.hostname}"
  }
}
