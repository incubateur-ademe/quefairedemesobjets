# Both containers run the same image against the same database and bucket, so
# the environment is defined once here. The worker overrides CONTAINER_ROLE.
locals {
  environment_variables = merge(
    {
      ENVIRONMENT             = var.environment
      BASE_URL                = var.BASE_URL
      ALLOWED_HOSTS           = var.ALLOWED_HOSTS
      AWS_STORAGE_BUCKET_NAME = var.AWS_STORAGE_BUCKET_NAME
      AWS_S3_REGION_NAME      = var.AWS_S3_REGION_NAME
      AWS_S3_ENDPOINT_URL     = var.AWS_S3_ENDPOINT_URL
      CONN_MAX_AGE            = tostring(var.CONN_MAX_AGE)
      GUNICORN_WORKERS        = tostring(var.GUNICORN_WORKERS)
      GUNICORN_THREADS        = tostring(var.GUNICORN_THREADS)
    },
    var.extra_environment_variables,
  )

  secret_environment_variables = merge(
    {
      DATABASE_URL                    = var.DATABASE_URL
      SECRET_KEY                      = var.SECRET_KEY
      NOTION_TOKEN                    = var.NOTION_TOKEN
      NOTION_CONTACT_FORM_DATABASE_ID = var.NOTION_CONTACT_FORM_DATABASE_ID
      AWS_ACCESS_KEY_ID               = var.AWS_ACCESS_KEY_ID
      AWS_SECRET_ACCESS_KEY           = var.AWS_SECRET_ACCESS_KEY
      SENTRY_DSN                      = var.SENTRY_DSN
    },
    var.POSTHOG_PERSONAL_API_KEY == null ? {} : { POSTHOG_PERSONAL_API_KEY = var.POSTHOG_PERSONAL_API_KEY },
    var.extra_secret_environment_variables,
  )
}

resource "scaleway_container" "webapp" {
  name = "${var.prefix}-${var.environment}-webapp"
  tags = concat(
    [
      var.environment,
      var.prefix,
      "webapp",
    ],
    var.extra_tags,
  )
  namespace_id   = local.namespace_id
  registry_image = var.registry_image
  port           = 8000
  cpu_limit      = var.cpu_limit
  memory_limit   = var.memory_limit
  min_scale      = var.min_scale
  max_scale      = var.max_scale
  timeout        = var.timeout
  privacy        = "public"
  protocol       = "http1"

  # Each instance serves workers x threads requests at once: scale out at
  # that point, not at the platform default, or requests queue in gunicorn.
  scaling_option {
    concurrent_requests_threshold = var.GUNICORN_WORKERS * var.GUNICORN_THREADS
  }

  # Without the database: an incident there must not restart every instance
  # at once.
  liveness_probe {
    http {
      path = "/livez/"
    }
    failure_threshold = 5
    interval          = "30s"
    timeout           = "10s"
  }

  # With the database: the container takes traffic once it can serve it. Up
  # to 5 minutes, for the entrypoint of a preview to run its migrations.
  startup_probe {
    http {
      path = "/healthz/"
    }
    failure_threshold = 10
    interval          = "30s"
    timeout           = "10s"
  }

  environment_variables        = local.environment_variables
  secret_environment_variables = local.secret_environment_variables
}
