variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "environment" {
  description = "Environnement de déploiement (ex: preview-<sha>)"
  type        = string
}

variable "project_id" {
  description = "ID du projet Scaleway (pour scoper l'IAM application)"
  type        = string
}

variable "object_expiration_days" {
  description = "Nombre de jours après lesquels les objets sont supprimés automatiquement"
  type        = number
  default     = 1
}
