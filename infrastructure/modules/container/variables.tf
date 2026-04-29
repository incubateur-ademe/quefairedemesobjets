variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}
variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "airflow_scheduler_registry_image" {
  type = string
}

variable "airflow_scheduler_cpu_limit" {
  type = number
}
variable "airflow_scheduler_memory_limit" {
  type = number
}
variable "airflow_scheduler_min_scale" {
  type = number
}
variable "airflow_scheduler_max_scale" {
  type = number
}
variable "airflow_scheduler_timeout" {
  type = number
}

variable "airflow_webserver_registry_image" {
  type = string
}

variable "airflow_webserver_cpu_limit" {
  type = number
}
variable "airflow_webserver_memory_limit" {
  type = number
}
variable "airflow_webserver_min_scale" {
  type = number
}
variable "airflow_webserver_max_scale" {
  type = number
}
variable "airflow_webserver_timeout" {
  type = number
}

variable "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" {
  type      = string
  sensitive = true
}
variable "AIRFLOW_CONN_WEBAPP_DB" {
  type      = string
  sensitive = true
}
variable "DATABASE_URL" {
  type      = string
  sensitive = true
}
variable "DB_WAREHOUSE" {
  type      = string
  sensitive = true
}
variable "DB_WEBAPP_SAMPLE" {
  type      = string
  sensitive = true
}
variable "ENVIRONMENT" {
  type      = string
  sensitive = true
}
variable "POSTGRES_DB" {
  type      = string
  sensitive = true
}
variable "POSTGRES_HOST" {
  type      = string
  sensitive = true
}
variable "POSTGRES_PASSWORD" {
  type      = string
  sensitive = true
}
variable "POSTGRES_PORT" {
  type      = string
  sensitive = true
}
variable "POSTGRES_SCHEMA" {
  type      = string
  sensitive = true
}
variable "POSTGRES_USER" {
  type      = string
  sensitive = true
}
variable "SCW_ACCESS_KEY" {
  type      = string
  sensitive = true
}
variable "SCW_DEFAULT_ORGANIZATION_ID" {
  type      = string
  sensitive = true
}
variable "SCW_DEFAULT_PROJECT_ID" {
  type      = string
  sensitive = true
}
variable "SCW_SECRET_KEY" {
  type      = string
  sensitive = true
}
variable "SECRET_KEY" {
  type      = string
  sensitive = true
}
variable "_AIRFLOW_WWW_USER_USERNAME" {
  type      = string
  sensitive = true
}
variable "_AIRFLOW_WWW_USER_PASSWORD" {
  type      = string
  sensitive = true
}
variable "AIRFLOW__WEBSERVER__INSTANCE_NAME" {
  type = string
}

# --- Variables additionnelles pour le scheduler ---
# Les DAGs importent du code Django et ont donc besoin du même environnement
# que le container webapp. Toutes optionnelles (default ""), donc preprod/prod
# qui n'ont pas encore migré ne voient aucun changement.

variable "BASE_URL" {
  description = "URL publique du webapp (utilisée par certains DAGs pour construire des liens absolus)"
  type        = string
  default     = ""
}

variable "ALLOWED_HOSTS" {
  description = "Hosts autorisés par Django (CSV) — couvre l'URL interne du container"
  type        = string
  default     = ""
}

variable "AWS_S3_REGION_NAME" {
  description = "Région S3 pour les écritures de DAGs (Scaleway = fr-par)"
  type        = string
  default     = ""
}

variable "AWS_S3_ENDPOINT_URL" {
  description = "Endpoint S3 (https://s3.fr-par.scw.cloud)"
  type        = string
  default     = ""
}

variable "AWS_STORAGE_BUCKET_NAME" {
  description = "Bucket S3 utilisé par les DAGs (différent du bucket de logs Airflow)"
  type        = string
  default     = ""
}

# --- Secret Manager opt-in ---
# Si true, le module lit AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, SENTRY_DSN,
# NOTION_TOKEN, POSTHOG_PERSONAL_API_KEY depuis Scaleway Secret Manager via
# data.scaleway_secret_version (voir secrets.tf).
# Si false (default, comportement preprod/prod actuel), aucun de ces secrets
# n'est passé au container.

variable "use_secret_manager" {
  description = "Activer la lecture des secrets webapp depuis Scaleway Secret Manager"
  type        = bool
  default     = false
}

variable "secret_name_AWS_ACCESS_KEY_ID" {
  type    = string
  default = "AWS_ACCESS_KEY_ID"
}

variable "secret_name_AWS_SECRET_ACCESS_KEY" {
  type    = string
  default = "AWS_SECRET_ACCESS_KEY"
}

variable "secret_name_SENTRY_DSN" {
  type    = string
  default = "SENTRY_DSN"
}

variable "secret_name_NOTION_TOKEN" {
  type    = string
  default = "NOTION_TOKEN"
}

variable "secret_name_POSTHOG_PERSONAL_API_KEY" {
  type    = string
  default = "POSTHOG_PERSONAL_API_KEY"
}