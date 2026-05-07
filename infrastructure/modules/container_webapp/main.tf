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
  privacy        = "public"
  protocol       = "http1"

  health_check {
    http {
      path = "/"
    }
    failure_threshold = 10
    interval          = "30s"
  }

  environment_variables = {
    ENVIRONMENT                     = var.environment
    DEBUG                           = "false"
    BASE_URL                        = var.base_url
    ALLOWED_HOSTS                   = var.allowed_hosts
    LEGACY_SITE_VITRINE_DOMAIN      = var.legacy_site_vitrine_domain
    AWS_S3_REGION_NAME              = "fr-par"
    AWS_S3_ENDPOINT_URL             = "https://s3.fr-par.scw.cloud"
    AWS_STORAGE_BUCKET_NAME         = var.webapp_bucket_name
    DISTANCE_MAX                    = var.distance_max
    DJANGO_IMPORT_EXPORT_LIMIT      = var.django_import_export_limit
    NOTION_CONTACT_FORM_DATABASE_ID = var.notion_contact_form_database_id
    CONTAINER_VERSION               = var.image_tag
  }

  secret_environment_variables = local.secrets
}
