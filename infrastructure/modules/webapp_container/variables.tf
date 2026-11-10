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
  validation {
    # An empty tag is what get_env("IMAGE_TAG", "") gives without IMAGE_TAG.
    condition     = can(regex(":[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.registry_image))
    error_message = "Set IMAGE_TAG. A new tag goes through the deploy workflow, which runs bin/post_deploy first; to apply without redeploying, use the tag of the registry_image output."
  }
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
  validation {
    condition     = var.DATABASE_URL != ""
    error_message = "DATABASE_URL is empty: check the outputs of the database stack."
  }
}

variable "SECRET_KEY" {
  type      = string
  sensitive = true
  validation {
    condition     = var.SECRET_KEY != ""
    error_message = "SECRET_KEY is empty: is the secret set in the GitHub environment?"
  }
}

variable "NOTION_TOKEN" {
  type      = string
  sensitive = true
}

variable "NOTION_CONTACT_FORM_DATABASE_ID" {
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
  validation {
    condition     = var.AWS_ACCESS_KEY_ID != ""
    error_message = "AWS_ACCESS_KEY_ID is empty: is the secret set in the GitHub environment?"
  }
}

variable "AWS_SECRET_ACCESS_KEY" {
  type      = string
  sensitive = true
  validation {
    condition     = var.AWS_SECRET_ACCESS_KEY != ""
    error_message = "AWS_SECRET_ACCESS_KEY is empty: is the secret set in the GitHub environment?"
  }
}

variable "AWS_STORAGE_BUCKET_NAME" {
  type    = string
  default = ""
}

variable "BASE_URL" {
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
  validation {
    condition     = alltrue([for v in values(var.extra_secret_environment_variables) : v != ""])
    error_message = "A secret environment variable is empty: is the secret set in the GitHub environment?"
  }
}

## Worker (django-tasks)

variable "worker_enabled" {
  description = "Previews run without a worker, as they did before"
  type        = bool
  default     = true
}

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
  default     = 4
}

variable "CONN_MAX_AGE" {
  description = "Persistent DB connections, in seconds. Defaults to 0 in settings/base.py, so it must be set explicitly here or the migration silently loses connection pooling."
  type        = number
  default     = 600
}
