variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "environment" {
  description = "Environnement de déploiement (ex: pr-123)"
  type        = string
}

variable "namespace_id" {
  description = "ID d'un namespace existant (preview le partage entre PRs). Si null, le module crée son propre namespace."
  type        = string
  default     = null
}

variable "registry_image" {
  description = "Image Docker complète (registry/namespace/image:tag)"
  type        = string
}

variable "extra_tags" {
  description = "Tags additionnels (ex: preview, preview-pr-123)"
  type        = list(string)
  default     = []
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

## Worker (django-tasks)

variable "worker_cpu_limit" {
  type    = number
  default = 1000
}

variable "worker_memory_limit" {
  type    = number
  default = 2048
}

variable "worker_min_scale" {
  description = "Keep at least 1: the worker polls the queue, it is not request-driven"
  type        = number
  default     = 1
}

variable "worker_max_scale" {
  type    = number
  default = 1
}

## Gunicorn

variable "GUNICORN_WORKERS" {
  type    = number
  default = 2
}

variable "GUNICORN_THREADS" {
  description = "Concurrency is workers x threads. Each thread holds a Postgres connection for CONN_MAX_AGE, so raising this consumes the max_connections budget shared with Airflow."
  type        = number
  default     = 8
}

variable "CONN_MAX_AGE" {
  description = "Persistent DB connections, in seconds. Defaults to 0 in settings/base.py, so it must be set explicitly here or the migration silently loses connection pooling."
  type        = number
  default     = 600
}
