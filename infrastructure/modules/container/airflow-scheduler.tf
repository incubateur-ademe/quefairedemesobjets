resource "scaleway_container" "airflow_scheduler" {
  name                = "${var.prefix}-airflow-scheduler"
  tags                = [var.environment, var.prefix, "airflow", "scheduler"]
  namespace_id        = scaleway_container_namespace.main.id
  registry_image      = var.airflow_scheduler_registry_image
  port                = 8974
  cpu_limit           = var.airflow_scheduler_cpu_limit
  memory_limit        = var.airflow_scheduler_memory_limit
  min_scale           = var.airflow_scheduler_min_scale
  max_scale           = var.airflow_scheduler_max_scale
  timeout             = var.airflow_scheduler_timeout
  deploy              = true
  privacy             = "public"
  protocol            = "http1"
  local_storage_limit = 10240 # 10 GB
  sandbox             = "v1"
  health_check {
    http {
      path = "/health"
    }
    failure_threshold = 5
    interval          = "30s"
  }

  environment_variables = {
    AIRFLOW__API__AUTH_BACKENDS                    = "airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session"
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION     = "true"
    AIRFLOW__CORE__DAGS_FOLDER                     = "/opt/airflow/dags"
    AIRFLOW__CORE__ENABLE_XCOM_PICKLING            = "true"
    AIRFLOW__CORE__EXECUTOR                        = "LocalExecutor"
    AIRFLOW__CORE__FERNET_KEY                      = ""
    AIRFLOW__CORE__LOAD_EXAMPLES                   = "false"
    AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES = var.AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES
    AIRFLOW__LOGGING__ENCRYPT_S3_LOGS              = "false"
    AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER       = "s3://${var.prefix}-${var.environment}-airflow"
    AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID           = "scalewaylogs"
    AIRFLOW__LOGGING__REMOTE_LOGGING               = "true"
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK        = "true"
    AIRFLOW__SCHEDULER__CATCHUP_BY_DEFAULT         = "false"
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG              = "true"
    AIRFLOW__WEBSERVER__WARN_DEPLOYMENT_EXPOSURE   = "false"
    ENVIRONMENT                                    = var.environment
  }
  secret_environment_variables = {
    AIRFLOW__CORE__EXECUTION_API_SERVER_URL = var.AIRFLOW__CORE__EXECUTION_API_SERVER_URL
    AIRFLOW__API_AUTH__JWT_SECRET           = var.AIRFLOW__API_AUTH__JWT_SECRET
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN     = var.AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
    AIRFLOW_CONN_WEBAPP_DB                  = var.AIRFLOW_CONN_WEBAPP_DB
    AIRFLOW_CONN_SCALEWAYLOGS               = var.AIRFLOW_CONN_SCALEWAYLOGS
    DATABASE_URL                            = var.DATABASE_URL
    DB_WAREHOUSE                            = var.DB_WAREHOUSE
    DB_WEBAPP_SAMPLE                        = var.DB_WEBAPP_SAMPLE
    ENVIRONMENT                             = var.ENVIRONMENT
    POSTGRES_DB                             = var.POSTGRES_DB
    POSTGRES_HOST                           = var.POSTGRES_HOST
    POSTGRES_PASSWORD                       = var.POSTGRES_PASSWORD
    POSTGRES_PORT                           = var.POSTGRES_PORT
    POSTGRES_SCHEMA                         = var.POSTGRES_SCHEMA
    POSTGRES_USER                           = var.POSTGRES_USER
    SCW_ACCESS_KEY                          = var.SCW_ACCESS_KEY
    SCW_DEFAULT_ORGANIZATION_ID             = var.SCW_DEFAULT_ORGANIZATION_ID
    SCW_DEFAULT_PROJECT_ID                  = var.SCW_DEFAULT_PROJECT_ID
    SCW_SECRET_KEY                          = var.SCW_SECRET_KEY
    SECRET_KEY                              = var.SECRET_KEY
  }
}