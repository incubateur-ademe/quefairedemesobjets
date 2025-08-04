resource "scaleway_registry_namespace" "main" {
  name        = "main"
  description = "Main container registry"
  is_public   = false
}