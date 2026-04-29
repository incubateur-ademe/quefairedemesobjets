variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "environment" {
  description = "Environnement de déploiement (ex: preprod, prod, preview-<sha>)"
  type        = string
}

variable "namespace_id" {
  description = "ID du namespace Scaleway Container où déployer le webapp"
  type        = string
}

variable "registry_image" {
  description = "Image Docker complète (registry/namespace/image:tag)"
  type        = string
}

variable "extra_tags" {
  description = "Tags additionnels (ex: preview-sha-abc1234, created-at-1735689600)"
  type        = list(string)
  default     = []
}

variable "domain_hostname" {
  description = "Hostname custom à attacher au container (ex: <sha>.quefairedemesdechets.incubateur.ademe.dev). Vide pour ne rien attacher."
  type        = string
  default     = ""
}

variable "cpu_limit" {
  type    = number
  default = 1000
}

variable "memory_limit" {
  type    = number
  default = 2048
}

variable "min_scale" {
  type    = number
  default = 0
}

variable "max_scale" {
  type    = number
  default = 1
}

variable "timeout" {
  type    = number
  default = 300
}

variable "DATABASE_URL" {
  type      = string
  sensitive = true
}

variable "SECRET_KEY" {
  type      = string
  sensitive = true
}

variable "ALLOWED_HOSTS" {
  type    = string
  default = ""
}

variable "AWS_ACCESS_KEY_ID" {
  type      = string
  sensitive = true
  default   = ""
}

variable "AWS_SECRET_ACCESS_KEY" {
  type      = string
  sensitive = true
  default   = ""
}

variable "AWS_STORAGE_BUCKET_NAME" {
  type    = string
  default = ""
}

variable "AWS_S3_REGION_NAME" {
  type    = string
  default = "fr-par"
}

variable "AWS_S3_ENDPOINT_URL" {
  type    = string
  default = "https://s3.fr-par.scw.cloud"
}

variable "SENTRY_DSN" {
  type      = string
  sensitive = true
  default   = ""
}

variable "extra_environment_variables" {
  description = "Variables d'environnement additionnelles non secrètes"
  type        = map(string)
  default     = {}
}

variable "extra_secret_environment_variables" {
  description = "Variables d'environnement additionnelles secrètes"
  type        = map(string)
  sensitive   = true
  default     = {}
}
