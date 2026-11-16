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
