resource "scaleway_container" "nginx" {
  name           = "${var.prefix}-${var.environment}-nginx"
  tags           = [var.environment, var.prefix, "nginx", "ingress"]
  namespace_id   = var.namespace_id
  registry_image = var.registry_image
  port           = 8080
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
    failure_threshold = 5
    interval          = "30s"
  }

  environment_variables = {
    PORT                       = "8080"
    BASE_DOMAIN                = var.base_domain
    UPSTREAM_HOST              = "${var.upstream_domain}:443"
    UPSTREAM_SCHEME            = "https"
    NGINX_DISABLE_CACHE        = var.disable_cache ? "1" : "0"
    LEGACY_SITE_VITRINE_DOMAIN = var.legacy_site_vitrine_domain
  }
}
