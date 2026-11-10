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
  value = concat(
    [for route in var.routes : route.hostname],
    var.webapp == null ? [] : var.webapp.domains,
  )
}

output "serves_webapp" {
  description = "Whether the gateway serves the webapp: a webapp deploy only redeploys it, to empty its cache, when it does"
  value       = var.webapp != null
}

output "public_endpoints" {
  description = "URL publiques routées par le gateway"
  value = {
    for name, route in var.routes :
    name => "https://${route.hostname}"
  }
}

output "registry_image" {
  description = "Image running now: pass its tag as IMAGE_TAG to apply by hand without redeploying"
  value       = scaleway_container.nginx.registry_image
}
