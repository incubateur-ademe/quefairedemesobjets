locals {
  route_environment_variables = merge(
    {
      ENVIRONMENT = var.environment
    },
    {
      for name, route in var.routes :
      "ROUTE_${upper(replace(name, "-", "_"))}_HOST" => route.hostname
    },
    {
      for name, route in var.routes :
      "ROUTE_${upper(replace(name, "-", "_"))}_UPSTREAM" => route.upstream
    },
  )
}

resource "scaleway_container" "nginx" {
  name           = "${var.prefix}-nginx"
  tags           = [var.environment, var.prefix, "nginx", "gateway"]
  namespace_id   = scaleway_container_namespace.main.id
  registry_image = var.nginx_registry_image
  port           = 8080
  cpu_limit      = var.nginx_cpu_limit
  memory_limit   = var.nginx_memory_limit
  min_scale      = var.nginx_min_scale
  max_scale      = var.nginx_max_scale
  timeout        = var.nginx_timeout
  deploy         = true
  privacy        = "public"
  protocol       = "http1"
  http_option    = "redirected"

  health_check {
    http {
      path = "/healthz"
    }
    failure_threshold = 5
    interval          = "30s"
  }

  environment_variables = local.route_environment_variables
}

# Each hostname needs to be attached for Scaleway to issue the ACME cert.
# The wildcard CNAME (*.quefairedemesobjets.ademe.fr or
# *.preprod.quefairedemesobjets.ademe.fr) must already point at
# scaleway_container.nginx.domain_name, otherwise HTTP-01 fails.
resource "scaleway_container_domain" "routes" {
  for_each     = var.routes
  container_id = scaleway_container.nginx.id
  hostname     = each.value.hostname
}
