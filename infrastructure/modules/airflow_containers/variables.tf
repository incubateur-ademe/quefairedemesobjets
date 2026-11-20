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
  validation {
    # An empty tag is what get_env("IMAGE_TAG", "") gives without IMAGE_TAG.
    # The three images share the tag: checked once.
    condition     = can(regex(":[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.airflow_scheduler_registry_image))
    error_message = "Set IMAGE_TAG to the tag to deploy. To apply without redeploying, use the tag of the registry_image output."
  }
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

variable "airflow_dag_processor_registry_image" {
  type = string
}

variable "airflow_dag_processor_cpu_limit" {
  type = number
}
variable "airflow_dag_processor_memory_limit" {
  type = number
}
variable "airflow_dag_processor_min_scale" {
  type = number
}
variable "airflow_dag_processor_max_scale" {
  type = number
}
variable "airflow_dag_processor_timeout" {
  type = number
}

variable "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" {
  type      = string
  sensitive = true
}
variable "AIRFLOW_METADATA_DB_URL" {
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
variable "SCW_SECRET_KEY" {
  type      = string
  sensitive = true
}
variable "SCW_SECRET_KEY_INFRA" {
  type      = string
  sensitive = true
}
variable "SCW_ACCESS_KEY_INFRA" {
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
variable "AIRFLOW_CONN_SCALEWAYLOGS" {
  type      = string
  sensitive = true
}
variable "AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES_REGEXP" {
  type = string
}
variable "AIRFLOW__DAG_PROCESSOR__MIN_FILE_PROCESS_INTERVAL" {
  type = number
}
variable "AIRFLOW__DAG_PROCESSOR__PARSING_PROCESSES" {
  type = number
}
variable "WEBAPP_URL" {
  description = "Webapp base URL for API calls from DAGs (parse time and runtime)"
  type        = string
}
variable "POSTHOG_PERSONAL_API_KEY" {
  description = "Clé API personnelle PostHog (requêtes HogQL depuis les DAGs)"
  type        = string
  sensitive   = true
}

variable "custom_domain" {
  description = "Public hostname served by the nginx gateway (e.g. airflow.preprod.quefairedemesobjets.ademe.fr). Used for Airflow BASE_URL. Null or empty keeps the Scaleway-generated domain in generated links."
  type        = string
  default     = null
  nullable    = true
}
