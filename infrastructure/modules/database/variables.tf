variable "project_id" {
  description = "ID du projet Scaleway"
  type        = string
}

variable "organization_id" {
  description = "ID de l'organisation Scaleway"
  type        = string
}

variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "db_password" {
  description = "Mot de passe de la base de données"
  type        = string
  sensitive   = true
}

variable "db_username" {
  description = "Nom d'utilisateur de la base de données"
  type        = string
  default     = "qfdmo"
}