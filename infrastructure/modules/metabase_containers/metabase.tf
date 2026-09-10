resource "scaleway_container" "metabase" {
  name           = "${var.prefix}-metabase"
  tags           = [var.environment, var.prefix, "metabase"]
  namespace_id   = scaleway_container_namespace.main.id
  registry_image = "${var.metabase_registry_image}:${var.tag_docker}"
  port           = 3000
  cpu_limit      = var.metabase_cpu_limit
  memory_limit   = var.metabase_memory_limit
  min_scale      = var.metabase_min_scale
  max_scale      = var.metabase_max_scale
  timeout        = var.metabase_timeout
  deploy         = true
  privacy        = "public"
  protocol       = "http1"

  # Metabase (JVM) met souvent plus d'une minute à démarrer.
  startup_probe {
    http {
      path = "/api/health"
    }
    failure_threshold = 20
    interval          = "10s"
    timeout           = "5s"
  }

  liveness_probe {
    http {
      path = "/api/health"
    }
    failure_threshold = 5
    interval          = "30s"
    timeout           = "10s"
  }

  environment_variables = {
    ENVIRONMENT            = var.environment
    MB_DB_TYPE             = "postgres"
    MB_JETTY_PORT          = "3000"
    MB_SITE_NAME           = var.MB_SITE_NAME
    MB_LOAD_SAMPLE_CONTENT = var.MB_LOAD_SAMPLE_CONTENT
    JAVA_TOOL_OPTIONS      = "-XX:MaxRAMPercentage=75.0"
  }

  secret_environment_variables = {
    MB_DB_CONNECTION_URI     = var.MB_DB_CONNECTION_URI
    MB_ENCRYPTION_SECRET_KEY = var.MB_ENCRYPTION_SECRET_KEY
  }
}
