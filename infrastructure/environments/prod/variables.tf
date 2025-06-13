variable "environment" {
  description = "Environment"
  type        = string
  default     = "prod"
}

variable "access_key" {
  description = "Clé d'accès à Scaleway"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Secret d'accès à Scaleway"
  type        = string
  sensitive   = true
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

variable "project_id" {
  description = "ID du projet Scaleway"
  type        = string
}

variable "organization_id" {
  description = "ID de l'organisation Scaleway"
  type        = string
}