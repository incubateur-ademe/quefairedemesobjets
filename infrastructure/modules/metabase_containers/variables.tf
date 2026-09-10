variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "metabase_registry_image" {
  description = "Image Docker Metabase (sans tag)"
  type        = string
  default     = "metabase/metabase"
}

variable "tag_docker" {
  description = "Tag Docker de l'image Metabase"
  type        = string
  default     = "v0.63.17.x"
}

variable "metabase_cpu_limit" {
  description = "CPU du container Metabase (millicores)"
  type        = number
}

variable "metabase_memory_limit" {
  description = "Mémoire du container Metabase (Mo)"
  type        = number
}

variable "metabase_min_scale" {
  description = "Nombre minimum d'instances Metabase"
  type        = number
}

variable "metabase_max_scale" {
  description = "Nombre maximum d'instances Metabase"
  type        = number
}

variable "metabase_timeout" {
  description = "Timeout du container Metabase (secondes)"
  type        = number
}

variable "MB_DB_CONNECTION_URI" {
  description = "URI PostgreSQL de la base applicative Metabase"
  type        = string
  sensitive   = true
}

variable "MB_ENCRYPTION_SECRET_KEY" {
  description = "Clé de chiffrement des secrets stockés par Metabase"
  type        = string
  sensitive   = true
}

variable "MB_SITE_NAME" {
  description = "Nom affiché de l'instance Metabase"
  type        = string
  default     = "Que Faire de Mes Objets"
}
