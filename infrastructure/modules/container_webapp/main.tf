resource "scaleway_container" "webapp" {
  name           = "${var.prefix}-${var.environment}-webapp"
  tags           = [var.environment, var.prefix, "webapp", "django"]
  namespace_id   = var.namespace_id
  registry_image = var.registry_image
  port           = 8000
  cpu_limit      = var.cpu_limit
  memory_limit   = var.memory_limit
  min_scale      = var.min_scale
  max_scale      = var.max_scale
  timeout        = var.timeout
  deploy         = true
  privacy        = "private"
  protocol       = "http1"

  health_check {
    http {
      path = "/"
    }
    failure_threshold = 5
    interval          = "30s"
  }

  environment_variables = {
    ENVIRONMENT             = var.environment
    DEBUG                   = "false"
    BASE_URL                = var.base_url
    ALLOWED_HOSTS           = var.allowed_hosts
    AWS_S3_REGION_NAME      = "fr-par"
    AWS_S3_ENDPOINT_URL     = "https://s3.fr-par.scw.cloud"
    AWS_STORAGE_BUCKET_NAME = var.webapp_bucket_name
    CONTAINER_VERSION       = var.image_tag
  }

  secret_environment_variables = local.secrets
}
