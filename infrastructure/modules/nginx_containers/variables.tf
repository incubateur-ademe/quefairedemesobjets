variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "nginx_registry_image" {
  description = "Image Docker du reverse-proxy nginx (registre:tag)"
  type        = string
  validation {
    # An empty tag is what get_env("IMAGE_TAG", "") gives without IMAGE_TAG.
    condition     = can(regex(":[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.nginx_registry_image))
    error_message = "Set IMAGE_TAG to the tag to deploy. To apply without redeploying, use the tag of the registry_image output."
  }
}

variable "nginx_cpu_limit" {
  description = "CPU du container nginx (millicores)"
  type        = number
}

variable "nginx_memory_limit" {
  description = "Mémoire du container nginx (Mo)"
  type        = number
}

variable "nginx_min_scale" {
  description = "Nombre minimum d'instances nginx"
  type        = number
}

variable "nginx_max_scale" {
  description = "Nombre maximum d'instances nginx"
  type        = number
}

variable "nginx_timeout" {
  description = "Timeout du container nginx (secondes)"
  type        = number
}

variable "routes" {
  description = "Services exposés via le gateway. hostname = FQDN public (sous-domaine du wildcard CNAME). upstream = domain_name natif Scaleway du backend, sans schéma."
  type = map(object({
    hostname = string
    upstream = string
  }))

  validation {
    condition = alltrue([
      for name, route in var.routes : (
        can(regex("^[a-z][a-z0-9_]*$", name))
        && can(regex("^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$", route.hostname))
        && can(regex("^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$", route.upstream))
      )
    ])
    error_message = "Route keys must be lowercase identifiers; hostname and upstream must be DNS names without scheme."
  }
}

variable "webapp" {
  description = <<-EOT
    Webapp served by the gateway from servers.conf.erb; null serves only the routes.
    upstream: public_endpoint of the webapp container. release: its registry_image,
    so that every webapp deploy redeploys the gateway and empties its cache.
    environment: production or staging, the values servers.conf.erb tests.
    server_names: base_domain and the aliases redirected to it. domains: host names
    attached to this container, whose CNAME must already resolve (ACME HTTP-01).
  EOT
  type = object({
    upstream     = string
    release      = string
    base_domain  = string
    environment  = string
    server_names = list(string)
    domains      = list(string)
  })
  default = null

  validation {
    condition = var.webapp == null ? true : (
      can(regex("^https://[a-z0-9]([a-z0-9.-]*[a-z0-9])?/?$", var.webapp.upstream))
      && can(regex(":[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.webapp.release))
      && can(regex("^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$", var.webapp.base_domain))
      && contains(["production", "staging"], var.webapp.environment)
    )
    error_message = "webapp: upstream must be https://<host>, release an image with its tag, base_domain a host name, environment production or staging."
  }

  validation {
    condition = var.webapp == null ? true : (
      contains(var.webapp.server_names, var.webapp.base_domain)
      && alltrue([
        for name in var.webapp.server_names :
        can(regex("^(\\*\\.)?[a-z0-9]([a-z0-9.-]*[a-z0-9])?$", name))
      ])
      && alltrue([
        for domain in var.webapp.domains :
        can(regex("^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$", domain))
        && contains(var.webapp.server_names, domain)
      ])
    )
    error_message = "webapp: server_names are host names (*.<host> allowed) and include base_domain; domains are host names listed in server_names."
  }
}

variable "webapp_auth_token" {
  description = "IAM secret key the gateway sends to the webapp as X-Auth-Token. Empty while the webapp is public."
  type        = string
  sensitive   = true
  nullable    = false
  default     = ""

  validation {
    # Checked again by 45-render-webapp.sh, but a key rejected there stops the
    # gateway at startup, and with it Airflow and Metabase.
    condition     = var.webapp_auth_token == "" || can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.webapp_auth_token))
    error_message = "webapp_auth_token must be empty or an IAM secret key (lowercase UUID)."
  }
}
