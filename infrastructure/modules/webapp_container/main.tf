# Captured once on first apply, preserved across re-applies of the same stack.
# Used by the cleanup workflow to age previews.
resource "time_static" "created_at" {}

resource "scaleway_container" "webapp" {
  name = "${var.prefix}-${var.environment}-webapp"
  tags = concat(
    [
      var.environment,
      var.prefix,
      "webapp",
      "created-at-${time_static.created_at.unix}",
    ],
    var.extra_tags,
  )
  namespace_id   = var.namespace_id
  registry_image = var.registry_image
  port           = 8000
  cpu_limit      = var.cpu_limit
  memory_limit   = var.memory_limit
  min_scale      = var.min_scale
  max_scale      = var.max_scale
  timeout        = var.timeout
  deploy         = true
  privacy        = "public"
  protocol       = "http1"

  health_check {
    http {
      path = "/healthz"
    }
    failure_threshold = 5
    interval          = "30s"
  }

  environment_variables = merge(
    {
      ENVIRONMENT             = var.environment
      ALLOWED_HOSTS           = var.ALLOWED_HOSTS
      AWS_STORAGE_BUCKET_NAME = var.AWS_STORAGE_BUCKET_NAME
      AWS_S3_REGION_NAME      = var.AWS_S3_REGION_NAME
      AWS_S3_ENDPOINT_URL     = var.AWS_S3_ENDPOINT_URL
    },
    var.extra_environment_variables,
  )

  secret_environment_variables = merge(
    {
      DATABASE_URL          = var.DATABASE_URL
      SECRET_KEY            = var.SECRET_KEY
      AWS_ACCESS_KEY_ID     = var.AWS_ACCESS_KEY_ID
      AWS_SECRET_ACCESS_KEY = var.AWS_SECRET_ACCESS_KEY
      SENTRY_DSN            = var.SENTRY_DSN
    },
    var.extra_secret_environment_variables,
  )
}

resource "scaleway_container_domain" "webapp" {
  count        = var.domain_hostname == "" ? 0 : 1
  container_id = scaleway_container.webapp.id
  hostname     = var.domain_hostname
}
