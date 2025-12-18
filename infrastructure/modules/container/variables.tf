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
variable "AIRFLOW__CORE__EXECUTION_API_SERVER_URL" {
  type      = string
  sensitive = true
}
variable "AIRFLOW__API_AUTH__JWT_SECRET" {
  type      = string
  sensitive = true
}
variable "AIRFLOW_CONN_SCALEWAYLOGS" {
  type      = string
  sensitive = true
}
variable "AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES" {
  type = string
}
