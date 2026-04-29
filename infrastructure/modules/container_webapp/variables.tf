variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "namespace_id" {
  description = "ID du namespace de containers Scaleway (réutilisé depuis le module container/airflow)"
  type        = string
}

variable "registry_image" {
  description = "Image Docker complète, ex. rg.fr-par.scw.cloud/ns-qfdmo/webapp:preview"
  type        = string
}

variable "image_tag" {
  description = "Tag de l'image, exposé à Django via CONTAINER_VERSION"
  type        = string
}

variable "cpu_limit" {
  description = "Limite CPU en mCPU (1000 = 1 vCPU)"
  type        = number
  default     = 1000
}

variable "memory_limit" {
  description = "Limite mémoire en MB"
  type        = number
  default     = 2048
}

variable "min_scale" {
  description = "Nombre minimum d'instances (0 = scale-to-zero)"
  type        = number
  default     = 0
}

variable "max_scale" {
  description = "Nombre maximum d'instances"
  type        = number
  default     = 1
}

variable "timeout" {
  description = "Timeout des requêtes en secondes"
  type        = number
  default     = 300
}

variable "base_url" {
  description = "URL publique de l'application (utilisée par Django pour les liens absolus). Vide jusqu'au second apply ; à renseigner avec l'URL nginx une fois connue."
  type        = string
  default     = ""
}

variable "allowed_hosts" {
  description = "Liste CSV des hosts autorisés par Django"
  type        = string
}

variable "webapp_bucket_name" {
  description = "Nom du bucket S3 pour les médias Django"
  type        = string
}

# Noms des secrets dans Scaleway Secret Manager.
# L'isolation par environnement est assurée par le project_id Scaleway (un
# projet par env), donc les secrets ont des noms bruts identiques d'un env
# à l'autre. Les valeurs sont lues à l'apply via data.scaleway_secret_version
# (voir secrets.tf) et injectées dans secret_environment_variables.
# Chaque secret doit exister dans le projet Scaleway avant le premier apply.

variable "secret_name_SECRET_KEY" {
  description = "Nom du secret Scaleway contenant SECRET_KEY (Django)"
  type        = string
  default     = "SECRET_KEY"
}

variable "secret_name_DATABASE_URL" {
  description = "Nom du secret Scaleway contenant DATABASE_URL (postgres://...)"
  type        = string
  default     = "DATABASE_URL"
}

variable "secret_name_DB_WAREHOUSE" {
  description = "Nom du secret Scaleway contenant DB_WAREHOUSE"
  type        = string
  default     = "DB_WAREHOUSE"
}

variable "secret_name_DB_WEBAPP_SAMPLE" {
  description = "Nom du secret Scaleway contenant DB_WEBAPP_SAMPLE"
  type        = string
  default     = "DB_WEBAPP_SAMPLE"
}

variable "secret_name_AWS_ACCESS_KEY_ID" {
  description = "Nom du secret Scaleway contenant AWS_ACCESS_KEY_ID (clé Scaleway pour S3)"
  type        = string
  default     = "AWS_ACCESS_KEY_ID"
}

variable "secret_name_AWS_SECRET_ACCESS_KEY" {
  description = "Nom du secret Scaleway contenant AWS_SECRET_ACCESS_KEY"
  type        = string
  default     = "AWS_SECRET_ACCESS_KEY"
}

variable "secret_name_SENTRY_DSN" {
  description = "Nom du secret Scaleway contenant SENTRY_DSN"
  type        = string
  default     = "SENTRY_DSN"
}

variable "secret_name_POSTHOG_PERSONAL_API_KEY" {
  description = "Nom du secret Scaleway contenant POSTHOG_PERSONAL_API_KEY"
  type        = string
  default     = "POSTHOG_PERSONAL_API_KEY"
}

variable "secret_name_NOTION_TOKEN" {
  description = "Nom du secret Scaleway contenant NOTION_TOKEN"
  type        = string
  default     = "NOTION_TOKEN"
}

variable "secret_name_ASSISTANT_POSTHOG_KEY" {
  description = "Nom du secret Scaleway contenant ASSISTANT_POSTHOG_KEY"
  type        = string
  default     = "ASSISTANT_POSTHOG_KEY"
}

variable "secret_name_CARTE_POSTHOG_KEY" {
  description = "Nom du secret Scaleway contenant CARTE_POSTHOG_KEY"
  type        = string
  default     = "CARTE_POSTHOG_KEY"
}
