variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}
variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "create_webapp_bucket" {
  description = "Si true, crée un bucket S3 dédié aux médias Django (Wagtail uploads). Activé pour preview ; à activer ultérieurement pour preprod/prod."
  type        = bool
  default     = false
}