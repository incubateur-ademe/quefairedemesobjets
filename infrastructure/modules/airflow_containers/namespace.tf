resource "scaleway_container_namespace" "main" {
  name = "${var.prefix}-${var.environment}"
}