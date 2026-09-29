resource "scaleway_container_namespace" "main" {
  name        = "${var.prefix}-${var.environment}-gateway"
  description = "Namespace nginx gateway (${var.environment})"
  tags        = [var.environment, var.prefix, "nginx", "gateway"]
}
