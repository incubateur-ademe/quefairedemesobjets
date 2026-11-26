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

  # Read by 45-render-webapp.sh. WEBAPP_RELEASE is read by nothing: it changes
  # on every webapp deploy, so Scaleway recreates the instances and their
  # nginx cache starts empty.
  webapp_environment_variables = var.webapp == null ? {} : {
    WEBAPP_UPSTREAM     = var.webapp.upstream
    WEBAPP_RELEASE      = var.webapp.release
    WEBAPP_BASE_DOMAIN  = var.webapp.base_domain
    WEBAPP_ENVIRONMENT  = var.webapp.environment
    WEBAPP_SERVER_NAMES = join(" ", var.webapp.server_names)
  }

  # null rather than {}: the gateway keeps the configuration it has today.
  webapp_secret_environment_variables = (
    var.webapp != null && var.webapp_auth_token != ""
    ? { WEBAPP_AUTH_TOKEN = var.webapp_auth_token }
    : null
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

  liveness_probe {
    http {
      path = "/healthz"
    }
    failure_threshold = 5
    interval          = "30s"
    timeout           = "10s"
  }

  lifecycle {
    precondition {
      condition     = var.webapp == null ? true : (var.webapp.privacy == "public" || var.webapp_auth_token != "")
      error_message = "The webapp is private but webapp_auth_token is empty: set webapp_auth_token in the secret of the stack and apply the gateway before making the webapp private."
    }
  }

  environment_variables = merge(
    local.route_environment_variables,
    local.webapp_environment_variables,
  )
  secret_environment_variables = local.webapp_secret_environment_variables
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

resource "scaleway_container_domain" "webapp" {
  for_each     = toset(var.webapp == null ? [] : var.webapp.domains)
  container_id = scaleway_container.nginx.id
  hostname     = each.value

  lifecycle {
    precondition {
      # Scaleway would only refuse the second domain at apply
      condition     = !contains([for route in var.routes : route.hostname], each.value)
      error_message = "${each.value} is both in routes and in webapp.domains."
    }
  }
}
