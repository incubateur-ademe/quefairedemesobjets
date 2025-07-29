variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "prefix" {
  description = "Prefix for the resources"
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
}

variable "warehouse_db_name" {
  description = "Nom de la base de données warehouse"
  type        = string
}

variable "node_type" {
  description = "Type de nœud de la base de données"
  type        = string
}

variable "volume_size" {
  description = "Taille du volume en GB"
  type        = number
}
