variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "environment" {
  description = "Environnement de déploiement (ex: pr-123)"
  type        = string
}

variable "object_expiration_days" {
  description = "Nombre de jours après lesquels les objets sont supprimés automatiquement"
  type        = number
  default     = 1
}
