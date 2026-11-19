locals {
  custom_domain_enabled = var.custom_domain != null && var.custom_domain != ""
}

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
    failure_threshold = 30
    interval          = "30s"
    timeout           = "10s"
  }

  liveness_probe {
    http {
      path = "/api/health"
    }
    failure_threshold = 5
    interval          = "30s"
    timeout           = "10s"
  }

  environment_variables = merge(
    {
      ENVIRONMENT            = var.environment
      MB_DB_TYPE             = "postgres"
      MB_JETTY_PORT          = "3000"
      MB_SITE_NAME           = var.MB_SITE_NAME
      MB_LOAD_SAMPLE_CONTENT = var.MB_LOAD_SAMPLE_CONTENT
      JAVA_TOOL_OPTIONS      = "-XX:MaxRAMPercentage=75.0"
    },
    local.custom_domain_enabled ? {
      MB_SITE_URL = "https://${var.custom_domain}"
    } : {},
  )

  secret_environment_variables = {
    MB_DB_CONNECTION_URI     = var.MB_DB_CONNECTION_URI
    MB_ENCRYPTION_SECRET_KEY = random_password.encryption_key.result
  }
}

# Metabase encrypts what it stores (database credentials) with this key: it is
# generated once and must never be replaced without re-encrypting.
resource "random_password" "encryption_key" {
  length  = 44
  special = false

  # A key adopted from before keeps its own shape
  lifecycle {
    ignore_changes  = all
    prevent_destroy = true
  }
}

# The key typed before it was generated here: while the stack secret still
# holds it, it is imported so that nothing changes. OpenTofu shows an import
# id in the plan: it appears once, in the output of that apply.
# To delete, with the variable, once prod is applied.
import {
  for_each = nonsensitive(var.MB_ENCRYPTION_SECRET_KEY != null) ? toset(["adopted"]) : toset([])
  to       = random_password.encryption_key
  id       = nonsensitive(var.MB_ENCRYPTION_SECRET_KEY)
}
