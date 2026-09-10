resource "scaleway_container_namespace" "main" {
  name        = "${var.prefix}-${var.environment}-metabase"
  description = "Namespace Metabase (${var.environment})"
  tags        = [var.environment, var.prefix, "metabase"]
}
