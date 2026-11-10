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

output "webapp_auth_token_set" {
  description = "Whether the gateway sends the IAM key to the webapp: the webapp deploy refuses to make the webapp private otherwise"
  value       = nonsensitive(var.webapp != null && var.webapp_auth_token != "")
}
