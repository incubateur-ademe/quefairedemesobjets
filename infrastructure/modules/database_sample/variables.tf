variable "instance_id" {
  description = "ID de l'instance RDB existante"
  type        = string
}

variable "db_name" {
  description = "Nom de la base de données à ajouter sur l'instance (optionnel)"
  type        = string
  default     = null
}

variable "db_username" {
  description = "Nom d'utilisateur de la base de données ajoutée"
  type        = string
}

variable "db_password" {
  description = "Mot de passe de la base de données ajoutée"
  type        = string
  sensitive   = true
}

variable "create_extensions_script_path" {
  description = "Chemin absolu vers le script SQL create_extensions.sql"
  type        = string
}

