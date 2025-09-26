resource "scaleway_container" "airflow_dag_processor" {
  name           = "${var.prefix}-airflow-dag-processor"
  tags           = [var.environment, var.prefix, "airflow", "dag-processor"]
  namespace_id   = scaleway_container_namespace.main.id
  registry_image = var.airflow_dag_processor_registry_image
  port           = 8974
  cpu_limit      = var.airflow_dag_processor_cpu_limit
  memory_limit   = var.airflow_dag_processor_memory_limit
  min_scale      = var.airflow_dag_processor_min_scale
  max_scale      = var.airflow_dag_processor_max_scale
  timeout        = var.airflow_dag_processor_timeout
  deploy         = true
  privacy        = "public"
  protocol       = "http1"

  environment_variables = {
    _AIRFLOW_DB_MIGRATE                          = "true"
    AIRFLOW__API__AUTH_BACKENDS                  = "airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session"
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION   = "true"
    AIRFLOW__CORE__DAGS_FOLDER                   = "/opt/airflow/dags"
    AIRFLOW__CORE__ENABLE_XCOM_PICKLING          = "true"
    AIRFLOW__CORE__EXECUTOR                      = "LocalExecutor"
    AIRFLOW__CORE__FERNET_KEY                    = ""
    AIRFLOW__CORE__LOAD_EXAMPLES                 = "false"
    AIRFLOW__LOGGING__ENCRYPT_S3_LOGS            = "false"
    AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER     = "s3://${var.prefix}-${var.environment}-airflow"
    AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID         = "scalewaylogs"
    AIRFLOW__LOGGING__REMOTE_LOGGING             = "true"
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK      = "true"
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG            = "true"
    AIRFLOW__WEBSERVER__WARN_DEPLOYMENT_EXPOSURE = "false"
  }
  secret_environment_variables = {
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = var.AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
    AIRFLOW_CONN_WEBAPP_DB              = var.AIRFLOW_CONN_WEBAPP_DB
    DATABASE_URL                        = var.DATABASE_URL
    DB_WAREHOUSE                        = var.DB_WAREHOUSE
    ENVIRONMENT                         = var.ENVIRONMENT
    POSTGRES_DB                         = var.POSTGRES_DB
    POSTGRES_HOST                       = var.POSTGRES_HOST
    POSTGRES_PASSWORD                   = var.POSTGRES_PASSWORD
    POSTGRES_PORT                       = var.POSTGRES_PORT
    POSTGRES_SCHEMA                     = var.POSTGRES_SCHEMA
    POSTGRES_USER                       = var.POSTGRES_USER
    SCW_ACCESS_KEY                      = var.SCW_ACCESS_KEY
    SCW_DEFAULT_ORGANIZATION_ID         = var.SCW_DEFAULT_ORGANIZATION_ID
    SCW_DEFAULT_PROJECT_ID              = var.SCW_DEFAULT_PROJECT_ID
    SCW_SECRET_KEY                      = var.SCW_SECRET_KEY
    SECRET_KEY                          = var.SECRET_KEY
  }
}