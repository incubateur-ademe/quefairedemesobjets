variable "environment" {
  description = "Environment"
  type        = string
  default     = "preview"
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
  default     = "lvao"
}

variable "tags" {
  description = "Tags for the resources"
  type        = list(string)
  default     = ["preview", "postgresql", "qfdmo", "warehouse", "dbt"]
}

variable "access_key" {
  description = "Clé d'accès à Scaleway"
  type        = string
}

variable "secret_key" {
  description = "Secret d'accès à Scaleway"
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

variable "db_name" {
  description = "Nom de la base de données"
  type        = string
  default     = "qfdmo"
}

variable "wh_db_name" {
  description = "Nom de la base de données warehouse"
  type        = string
  default     = "warehouse"
}

variable "project_id" {
  description = "ID du projet Scaleway"
  type        = string
}

variable "organization_id" {
  description = "ID de l'organisation Scaleway"
  type        = string
}