resource "scaleway_registry_namespace" "ns-qfdmo" {
  name      = "ns-qfdmo"
  is_public = false
}

# ML-deduplication inference images. Single shared namespace, hosted in the
# qfdmod-prod project, with env discrimination done through image names
# (see .github/workflows/ml-deduplication-inference-build-and-push.yml).
resource "scaleway_registry_namespace" "ns-ml-deduplication-inference" {
  name      = "ns-ml-deduplication-inference"
  is_public = false
}