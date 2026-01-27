resource "scaleway_container" "airflow_webserver" {
  name           = "${var.prefix}-airflow-webserver"
  tags           = [var.environment, var.prefix, "airflow", "webserver"]
  namespace_id   = scaleway_container_namespace.main.id
  registry_image = var.airflow_webserver_registry_image
  port           = 8080
  cpu_limit      = var.airflow_webserver_cpu_limit
  memory_limit   = var.airflow_webserver_memory_limit
  min_scale      = var.airflow_webserver_min_scale
  max_scale      = var.airflow_webserver_max_scale
  timeout        = var.airflow_webserver_timeout
  deploy         = true
  privacy        = "public"
  protocol       = "http1"

  health_check {
    http {
      path = "/api/v1/health"
    }
    failure_threshold = 5
    interval          = "30s"
  }

  environment_variables = {
    _AIRFLOW_DB_MIGRATE                          = "true"
    _AIRFLOW_WWW_USER_CREATE                     = "true"
    _PIP_ADDITIONAL_REQUIREMENTS                 = ""
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
    AIRFLOW__WEBSERVER__INSTANCE_NAME            = var.AIRFLOW__WEBSERVER__INSTANCE_NAME
    AIRFLOW__WEBSERVER__WORKERS                  = "1"
    AIRFLOW__WEBSERVER__WARN_DEPLOYMENT_EXPOSURE = "false"
    AIRFLOW__WEBSERVER__X_FRAME_ENABLED          = "false"
    ENVIRONMENT                                  = var.environment
  }
  secret_environment_variables = {
    _AIRFLOW_WWW_USER_USERNAME          = var._AIRFLOW_WWW_USER_USERNAME
    _AIRFLOW_WWW_USER_PASSWORD          = var._AIRFLOW_WWW_USER_PASSWORD
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = var.AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
    DATABASE_URL                        = var.DATABASE_URL
    DB_WAREHOUSE                        = var.DB_WAREHOUSE
    AIRFLOW_CONN_WEBAPP_DB              = var.AIRFLOW_CONN_WEBAPP_DB
  }
}