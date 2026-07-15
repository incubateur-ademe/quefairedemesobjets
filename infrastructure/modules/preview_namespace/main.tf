resource "scaleway_container_namespace" "preview" {
  name        = "${var.prefix}-${var.environment}"
  description = "Namespace partagé pour les containers des environnements de preview (un container par PR)"
  tags        = ["preview"]
}
